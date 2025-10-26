import asyncio
import datetime
import os
import json
import logging
import sys
from urllib.parse import urljoin, urlparse
from contextlib import asynccontextmanager
from collections import OrderedDict
from typing import Dict, Optional, Set

import aiofiles
import httpx
from bs4 import BeautifulSoup, SoupStrainer, NavigableString
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, HttpUrl
from playwright.async_api import async_playwright
from dotenv import load_dotenv

# ✅ Load environment variables from a .env file for security
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'), override=True)
print("Loaded key:", os.getenv("GROQ_API_KEY"))

# Logging with more detail
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- Models ---
class ScrapeRequest(BaseModel):
    url: HttpUrl

class ScrapeResponse(BaseModel):
    status: str
    message: str
    pages_found: int
    results: Optional[Dict[str, str]] = None
    pdf_filename: Optional[str] = None


# --- Global State & Lifespan Management ---
_browser = None

async def get_browser():
    global _browser
    if _browser is None:
        playwright = await async_playwright().start()
        _browser = await playwright.chromium.launch(
            headless=True,
            args=['--disable-blink-features=AutomationControlled']  # Help with bot detection
        )
    return _browser

async def shutdown_browser():
    global _browser
    if _browser:
        await _browser.close()
        _browser = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Browser will be initialized on first use
    yield
    # This block runs on shutdown
    await shutdown_browser()

# --- FastAPI App Initialization ---
app = FastAPI(
    title="Documentation Scraper API",
    description="An API to scrape and process documentation websites",
    version="2.1.0",  # ⚡ Updated: Performance optimizations applied
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("scraped_data", exist_ok=True)

# --- Enhanced Scraping Logic ---

async def extract_links_from_section(page, section_url, section_prefix):
    """Extract all documentation links from a section page"""
    # Normalize section_url by removing fragment if present
    parsed_section = urlparse(section_url)
    section_url = parsed_section._replace(fragment='').geturl()
    
    logger.info(f"Navigating to section: {section_url}")
    try:
        # Wait for network to be idle to allow JS-heavy sites to load
        await page.goto(section_url, timeout=45000, wait_until="networkidle")
        
        # Wait for common documentation containers
        try:
            await page.wait_for_selector('article, main, .content, #content', timeout=5000)
        except:
            logger.debug("No common content containers found, proceeding anyway")
        
    except Exception as e:
        logger.warning(f"Error navigating to {section_url}: {str(e)}")
        return []

    links = []
    seen = {section_url}  # Add the starting URL to avoid scraping it twice if linked
    base_domain = urlparse(section_url).netloc
    
    # Try multiple strategies to find links
    selectors = [
        'a[href]',  # All links
        'nav a[href]',  # Navigation links
        '.sidebar a[href]',  # Sidebar links
        '[role="navigation"] a[href]',  # Accessible navigation
        '.docs-sidebar a[href]',  # Common docs pattern
        '.menu a[href]',  # Menu links
    ]
    
    all_hrefs = set()
    # Use page.evaluate to extract hrefs directly, avoiding element handle issues
    try:
        for selector in selectors:
            try:
                hrefs = await page.evaluate('''
                    (selector) => {
                        const elements = document.querySelectorAll(selector);
                        return Array.from(elements).map(el => el.getAttribute('href')).filter(href => href);
                    }
                ''', selector)
                all_hrefs.update(hrefs)
            except Exception as e:
                logger.debug(f"Error with selector {selector}: {e}")
                continue
    except Exception as e:
        logger.warning(f"Error extracting links: {e}")
        # Fallback: try to get at least some links
        return [section_url]
    
    for href in all_hrefs:
        if not href:
            continue
        
        # Skip anchor links that only have fragments (like #section)
        if href.startswith('#'):
            continue
        
        full_url = urljoin(section_url, href)
        parsed_url = urlparse(full_url)
        
        # Remove fragment (anchor) from URL to avoid duplicates
        # e.g., https://docs.agno.com/page#section becomes https://docs.agno.com/page
        url_without_fragment = parsed_url._replace(fragment='').geturl()
        
        # More flexible filter: same domain, part of the same doc section, and not yet seen
        if (parsed_url.netloc == base_domain and
            parsed_url.path.startswith(f"/{section_prefix}") and
            url_without_fragment not in seen and
            not url_without_fragment.endswith(('.pdf', '.zip', '.png', '.jpg', '.jpeg', '.gif'))):  # Skip non-HTML resources
            links.append(url_without_fragment)
            seen.add(url_without_fragment)
    
    logger.info(f"Found {len(links)} unique links in section {section_prefix}")
    
    # Ensure the initial page is always first in the list to be scraped
    return [section_url] + links


async def extract_content_from_page(page, url):
    """Extract and convert page content to markdown with improved parsing"""
    try:
        logger.info(f"Extracting content from: {url}")
        # Wait for network idle to ensure JS-rendered content is loaded
        await page.goto(url, timeout=45000, wait_until="networkidle")
        
        # Wait for content to load
        try:
            await page.wait_for_selector('article, main, .content, #content, .documentation-content, .markdown-body', timeout=5000)
        except:
            logger.debug(f"No specific content container found for {url}, using body")

        content = await page.content()
        soup = BeautifulSoup(content, "html.parser")

        # Try to find the main content container with multiple strategies
        main_content = None
        content_selectors = [
            'main',
            'article',
            '[role="main"]',
            '.content',
            '.documentation',
            '.docs-content',
            '.markdown-body',
            '#content',
            '.doc-content',
            '.page-content'
        ]
        
        for selector in content_selectors:
            main_content = soup.select_one(selector)
            if main_content:
                logger.debug(f"Using content container: {selector}")
                break
        
        if not main_content:
            main_content = soup.body
            logger.debug("Using body as content container")
        
        if not main_content:
            return "No main content container found."

        # Remove navigation, sidebar, and non-content elements
        selectors_to_remove = [
            # Navigation elements
            "nav", ".nav", ".navbar", ".navigation", "[role='navigation']",
            ".sidebar", ".side-bar", ".menu", ".toc", ".table-of-contents",
            ".breadcrumb", ".breadcrumbs", ".pagination",
            
            # Header and footer elements
            "header", ".header", "footer", ".footer", "[role='contentinfo']", "[role='banner']",
            
            # Interactive elements
            ".cookie", ".modal", ".popup", ".lightbox", ".overlay",
            ".search", ".search-box", ".site-search", ".search-form",
            ".edit-page-link", ".edit-link", ".github-link", ".edit-on-github",
            
            # Ads and promotional content
            ".ad", ".advertisement", ".sponsored", ".promo", ".banner", ".announcement",
            
            # Hidden elements
            ".hidden", "[style*='display:none']", "[style*='visibility:hidden']",
            
            # Scripts and styles
            "script", "style", "noscript",
            
            # Social and sharing elements
            ".social", ".share", ".sharing", ".follow",
            
            # Page controls and utilities
            ".page-controls", ".utility", ".tools", ".actions",
            ".sticky-header", ".floating", ".fixed",
            
            # Comments and feedback
            ".comments", ".feedback", ".rating"
        ]

        for selector in selectors_to_remove:
            for unwanted in main_content.select(selector):
                # Do not remove if it's an inline element with content
                if unwanted.name in ['span', 'strong', 'em', 'b', 'i', 'code']:
                    continue
                # Also skip if it has significant text (e.g., a warning in a banner you want to keep)
                if len(unwanted.get_text(strip=True)) > 30:
                    continue
                unwanted.decompose()

        # Extract title
        title = soup.find("title")
        if title:
            title_text = title.get_text(strip=True)
            title_text = title_text.split('|')[0].split('-')[0].strip()
        else:
            h1_tag = main_content.find("h1")
            if h1_tag:
                title_text = h1_tag.get_text(strip=True)
            else:
                title_text = urlparse(url).path.split('/')[-1] or "Untitled Page"

        # Process content with improved parsing
        text_parts = [f"# {title_text}"]
        processed_elements: Set[int] = set()
        seen_content: Set[str] = set()  # Track unique content to prevent duplicates

        def process_inline_elements(element):
            """Process inline elements within a parent element"""
            if isinstance(element, NavigableString):
                return str(element).strip()
            result = []
            for child in element.children:
                if isinstance(child, NavigableString):
                    text = str(child).strip()
                    if text:
                        result.append(text)
                elif hasattr(child, 'name'):
                    # Skip block-level elements that should be processed separately
                    if child.name in ['ul', 'ol', 'table', 'pre', 'blockquote', 'div', 'section', 'article']:
                        continue
                    # Skip already processed elements (but allow re-reading for inline context)
                    if child.name in ["strong", "b"]:
                        inner_content = process_inline_elements(child)
                        if not inner_content:
                            inner_content = child.get_text(strip=True)
                        if inner_content:
                            result.append(f"**{inner_content}**")
                    elif child.name in ["em", "i"]:
                        inner_content = process_inline_elements(child)
                        if not inner_content:
                            inner_content = child.get_text(strip=True)
                        if inner_content:
                            result.append(f"*{inner_content}*")
                    elif child.name == "code":
                        text = child.get_text(strip=True)
                        if text:
                            result.append(f"`{text}`")
                    elif child.name == "a":
                        href = child.get('href')
                        text = child.get_text(strip=True)
                        if text:
                            if href and not href.startswith('#'):
                                full_url = urljoin(url, href)
                                result.append(f"[{text}]({full_url})")
                            else:
                                result.append(text)
                    elif child.name == "br":
                        result.append("\n")
                    elif child.name == "span":
                        # Process span content recursively
                        span_content = process_inline_elements(child)
                        if span_content:
                            result.append(span_content)
                    elif child.name in ["p", "div"]:
                        # Handle nested paragraphs or divs within inline contexts
                        nested_content = process_inline_elements(child)
                        if nested_content:
                            result.append(nested_content)
                    else:
                        # For other inline elements, try to get nested content first
                        nested_content = process_inline_elements(child)
                        if nested_content:
                            result.append(nested_content)
                        else:
                            # Fallback to just getting the text
                            text = child.get_text(strip=True)
                            if text:
                                result.append(text)
            return " ".join(filter(None, result))

        def process_element(el, parent_processed=False, depth=0):
            """Process an element and return its markdown representation"""
            if id(el) in processed_elements:
                return None
            
            # Skip if element has no text (but be careful with elements that might have children)
            element_text = el.get_text(strip=True)
            if not element_text:
                return None
            
            # Mark as processed early to prevent reprocessing
            processed_elements.add(id(el))
            
            # Handle different element types
            if el.name == "h1":
                text = el.get_text(strip=True)
                if text != title_text:  # Skip if it's the same as page title
                    return f"\n# {text}\n"
            elif el.name == "h2":
                return f"\n## {el.get_text(strip=True)}\n"
            elif el.name == "h3":
                return f"\n### {el.get_text(strip=True)}\n"
            elif el.name == "h4":
                return f"\n#### {el.get_text(strip=True)}\n"
            elif el.name == "h5":
                return f"\n##### {el.get_text(strip=True)}\n"
            elif el.name == "h6":
                return f"\n###### {el.get_text(strip=True)}\n"
            elif el.name == "p":
                # Process inline elements within paragraph
                content = process_inline_elements(el)
                return content + "\n" if content else None
            elif el.name == "pre":
                code = el.find("code")
                if code:
                    # Try to detect language from class
                    lang = ""
                    if code.get("class"):
                        classes = code.get("class")
                        for cls in classes:
                            if "language-" in cls:
                                lang = cls.split("language-")[1].split()[0]
                                break
                    return f"\n```{lang}\n{code.get_text()}\n```\n"
                return f"\n```\n{el.get_text()}\n```\n"
            elif el.name == "code" and not parent_processed:
                # Inline code
                return f"`{el.get_text(strip=True)}`"
            elif el.name == "ul":
                return process_list(el, ordered=False, depth=depth)
            elif el.name == "ol":
                return process_list(el, ordered=True, depth=depth)
            elif el.name == "blockquote":
                # Process blockquote with inline elements preserved
                blockquote_parts = []
                for child in el.children:
                    if hasattr(child, 'name'):
                        # Skip if already processed
                        if id(child) not in processed_elements:
                            child_result = process_element(child, parent_processed=True, depth=depth)
                            if child_result:
                                # Add > prefix to each line of the child result
                                for line in child_result.split('\n'):
                                    if line.strip():
                                        blockquote_parts.append(f"> {line}")
                    elif isinstance(child, NavigableString):
                        text = str(child).strip()
                        if text:
                            blockquote_parts.append(f"> {text}")
                return "\n".join(blockquote_parts) + "\n" if blockquote_parts else None
            elif el.name == "table":
                return process_table(el)
            elif el.name in ["strong", "b"]:
                # Process strong/bold tags even if they contain nested elements
                content = process_inline_elements(el)
                if content:
                    # If it's already formatted, return as is, otherwise make it bold
                    if not content.startswith('**'):
                        return f"**{content}**"
                    return content
            elif el.name in ["em", "i"]:
                content = process_inline_elements(el)
                if content:
                    if not content.startswith('*'):
                        return f"*{content}*"
                    return content
            elif el.name == "a" and not parent_processed:
                href = el.get('href')
                text = el.get_text(strip=True)
                if href and not href.startswith('#'):
                    full_url = urljoin(url, href)
                    return f"[{text}]({full_url})"
                return text
            elif el.name == "img":
                alt_text = el.get('alt', '')
                src = el.get('src', '')
                if src:
                    full_url = urljoin(url, src)
                    return f"![{alt_text or 'Image'}]({full_url})"
            elif el.name == "hr":
                return "\n---\n"
            elif el.name == "span":
                # Process span elements properly - they often contain important content
                content = process_inline_elements(el)
                if content:
                    return content
            elif el.name in ["div", "section", "article", "main", "aside", "tip", "note", "warning", "info"]:
                # For container elements, process their children
                # Check if this is a special component (like Tip, Note, etc.)
                element_class = el.get('class', [])
                element_id = el.get('id', '')
                
                # Handle special documentation components
                is_tip = el.name.lower() == 'tip' or 'tip' in str(element_class).lower()
                is_note = el.name.lower() == 'note' or 'note' in str(element_class).lower()
                is_warning = el.name.lower() == 'warning' or 'warning' in str(element_class).lower()
                
                results = []
                
                # Add component header if it's a special component
                if is_tip:
                    results.append("\n💡 **Tip:**\n")
                elif is_note:
                    results.append("\n📝 **Note:**\n")
                elif is_warning:
                    results.append("\n⚠️ **Warning:**\n")
                
                for child in el.children:
                    if hasattr(child, 'name'):
                        # Skip if already processed
                        if id(child) not in processed_elements:
                            result = process_element(child, depth=depth)
                            if result:
                                results.append(result)
                    elif isinstance(child, NavigableString):
                        text = str(child).strip()
                        if text and len(text) > 1:  # Skip single character strings
                            results.append(text)
                return "\n".join(results) if results else None
            elif el.name == "dl":
                # Definition lists
                return process_definition_list(el)
            elif el.name == "details":
                # Collapsible content
                summary = el.find("summary")
                if summary:
                    content = f"\n<details>\n<summary>{summary.get_text(strip=True)}</summary>\n\n"
                    for child in el.children:
                        if hasattr(child, 'name') and child.name != "summary":
                            # Skip if already processed
                            if id(child) not in processed_elements:
                                result = process_element(child, depth=depth)
                                if result:
                                    content += result
                    content += "\n</details>\n"
                    return content
            else:
                # For any other tags, try to extract their content
                content = process_inline_elements(el)
                if content:
                    return content
            
            return None

        def process_list(ul_ol, ordered=False, depth=0):
            """Process ul/ol lists"""
            # Mark the list itself as processed
            if id(ul_ol) in processed_elements:
                return ""
            processed_elements.add(id(ul_ol))
            
            items = []
            counter = 1
            for li in ul_ol.find_all("li", recursive=False):
                # Skip if already processed
                if id(li) in processed_elements:
                    continue
                processed_elements.add(id(li))
                
                # Process the list item content using process_inline_elements
                li_content = process_inline_elements(li)
                
                # Also check for nested lists
                nested_lists = []
                for child in li.find_all(["ul", "ol"], recursive=False):
                    if id(child) not in processed_elements:
                        nested = process_list(child, ordered=(child.name == "ol"), depth=depth+1)
                        if nested:
                            nested_lists.append(nested)
                
                if li_content or nested_lists:
                    indent = "  " * depth
                    if ordered:
                        item_text = f"{indent}{counter}. {li_content}"
                        counter += 1
                    else:
                        item_text = f"{indent}- {li_content}"
                    
                    items.append(item_text)
                    for nested in nested_lists:
                        items.append(nested)
            
            return "\n".join(items) + "\n" if items else ""

        def process_table(table):
            """Process HTML tables to markdown"""
            # Mark the table as processed to prevent duplicates
            if id(table) in processed_elements:
                return ""
            processed_elements.add(id(table))
            
            rows = []
            headers = []
            
            # Process header
            thead = table.find("thead")
            if thead:
                for th in thead.find_all("th"):
                    header_content = process_inline_elements(th)
                    headers.append(header_content or th.get_text(strip=True))
            else:
                # Check first row for headers
                first_row = table.find("tr")
                if first_row:
                    ths = first_row.find_all("th")
                    if ths:
                        for th in ths:
                            header_content = process_inline_elements(th)
                            headers.append(header_content or th.get_text(strip=True))
            
            if headers:
                rows.append("| " + " | ".join(headers) + " |")
                rows.append("|" + "|".join(["---" for _ in headers]) + "|")
            
            # Process body
            tbody = table.find("tbody") or table
            for tr in tbody.find_all("tr"):
                cells = []
                for td in tr.find_all(["td", "th"]):
                    cell_content = process_inline_elements(td)
                    if not cell_content:
                        cell_content = td.get_text(strip=True)
                    cell_text = cell_content.replace("|", "\\|")  # Escape pipes
                    cells.append(cell_text)
                if cells and not (headers and cells == headers):  # Skip if it's the header row
                    rows.append("| " + " | ".join(cells) + " |")
            
            return "\n" + "\n".join(rows) + "\n" if rows else ""

        def process_definition_list(dl):
            """Process definition lists"""
            # Mark the definition list as processed
            if id(dl) in processed_elements:
                return ""
            processed_elements.add(id(dl))
            
            result = []
            for child in dl.children:
                if hasattr(child, 'name'):
                    if id(child) not in processed_elements:
                        processed_elements.add(id(child))
                        if child.name == "dt":
                            content = process_inline_elements(child)
                            result.append(f"\n**{content or child.get_text(strip=True)}**")
                        elif child.name == "dd":
                            content = process_inline_elements(child)
                            result.append(f": {content or child.get_text(strip=True)}")
            return "\n".join(result) + "\n" if result else ""

        # Process only direct children of main content to avoid duplicates
        for element in main_content.children:
            if hasattr(element, 'name') and element.name:
                # Skip if already processed
                if id(element) not in processed_elements:
                    result = process_element(element)
                    if result and result.strip():
                        # Create a normalized version for duplicate detection
                        normalized = result.strip().lower()
                        # Only add if we haven't seen this exact content before
                        if normalized not in seen_content:
                            text_parts.append(result)
                            seen_content.add(normalized)

        # Join and clean up the output
        content = "\n".join(text_parts)
        
        # Advanced cleanup to remove duplicates and improve formatting
        import re
        
        # Remove excessive newlines (more than 2 consecutive)
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        # Remove duplicate lines that appear consecutively
        lines = content.split('\n')
        cleaned_lines = []
        prev_line = None
        seen_lines = set()
        
        for line in lines:
            stripped_line = line.strip()
            # Skip empty lines that repeat
            if stripped_line == '' and prev_line == '':
                continue
            # Skip lines that are exact duplicates of the previous line
            if stripped_line != prev_line:
                cleaned_lines.append(line.rstrip())
            prev_line = stripped_line
        
        content = "\n".join(cleaned_lines)
        
        # Remove repetitive patterns in code blocks
        content = re.sub(r'(```[\s\S]*?)\n(\1)', r'\1', content)
        
        # Clean up repetitive markdown patterns (headings, links)
        content = re.sub(r'(#+\s+[^\n]+)\n+\1', r'\1', content)
        
        # Remove repetitive link patterns
        content = re.sub(r'(\[[^\]]+\]\([^)]+\))\s+\1', r'\1', content)
        
        # Remove duplicate paragraphs (more aggressive deduplication)
        paragraphs = content.split('\n\n')
        unique_paragraphs = []
        seen_paragraph_hashes = set()
        
        for paragraph in paragraphs:
            # Normalize the paragraph for comparison
            normalized_para = paragraph.strip().lower()
            # Create a simple hash to detect duplicates
            para_hash = hash(normalized_para)
            
            # Only add if we haven't seen this paragraph before
            if para_hash not in seen_paragraph_hashes and normalized_para:
                unique_paragraphs.append(paragraph)
                seen_paragraph_hashes.add(para_hash)
        
        content = '\n\n'.join(unique_paragraphs)
        
        # Additional line-by-line deduplication for remaining duplicates
        lines = content.split('\n')
        seen_line_hashes = set()
        unique_lines = []
        
        for line in lines:
            stripped = line.strip()
            if stripped:  # Non-empty line
                # Create hash for comparison
                line_hash = hash(stripped.lower())
                # Skip if we've seen this exact line before (unless it's a very short line like markdown list marker)
                if line_hash not in seen_line_hashes or len(stripped) < 3:
                    unique_lines.append(line)
                    seen_line_hashes.add(line_hash)
            else:  # Empty line - always keep for formatting
                # But avoid multiple consecutive empty lines
                if unique_lines and unique_lines[-1].strip():
                    unique_lines.append(line)
        
        content = '\n'.join(unique_lines)
        
        # Log extraction success
        logger.info(f"Successfully extracted {len(content)} characters from {url}")
        
        return content.strip()

    except Exception as e:
        logger.error(f"Failed to extract content from {url}: {str(e)}", exc_info=True)
        return f"⚠️ Failed to process {url}: {str(e)}"


def convert_to_markdown(results: Dict[str, str]) -> str:
    """Convert the scraped results to a clean Markdown format"""
    markdown_content = []
    
    for url, content in results.items():
        # Add a heading with the URL as a link
        markdown_content.append(f"# Source: [{url}]({url})\n")
        # Add the content with proper formatting
        markdown_content.append(content)
        # Add a horizontal separator between different pages
        markdown_content.append("\n---\n")
    
    return "\n".join(markdown_content)


async def scrape_section(base_url, section):
    """Main function to scrape a documentation section"""
    section_url = f"{base_url}/{section}"
    ordered_results = OrderedDict()
    browser = await get_browser()

    # Create context with anti-detection measures and speed optimizations
    context = await browser.new_context(
        viewport={"width": 1920, "height": 1080},
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        locale='en-US',
        timezone_id='America/New_York',
        # ⚡ OPTIMIZED: Ignore HTTPS errors for speed
        ignore_https_errors=True
    )
    
    # ⚡ OPTIMIZED: Block images, CSS, fonts, media for maximum speed (70% bandwidth reduction)
    await context.route("**/*", lambda route: (
        route.abort() if route.request.resource_type in ["image", "stylesheet", "font", "media"]
        else route.continue_()
    ))

    try:
        # Extract links from the section
        page = await context.new_page()
        try:
            links = await extract_links_from_section(page, section_url, section)
            logger.info(f"Found {len(links)} page(s) under section /{section}")
        finally:
            await page.close()

        if not links:
            links = [section_url]  # Fallback to scraping just the entry page

        # Function to scrape individual pages with retry logic
        async def scrape_page_task(link, max_retries=2):
            page = await context.new_page()
            retries = 0
            last_error = None
            
            try:
                while retries <= max_retries:
                    try:
                        content = await extract_content_from_page(page, link)
                        return (link, content)
                    except Exception as e:
                        last_error = e
                        retries += 1
                        if retries <= max_retries:
                            # ⚡ OPTIMIZED: Quick retry with exponential backoff
                            wait_time = 0.5 * (2 ** (retries - 1))  # 0.5s, 1s
                            logger.warning(f"Retry {retries}/{max_retries} for {link} after {wait_time}s")
                            await asyncio.sleep(wait_time)
                        else:
                            logger.error(f"Failed after {max_retries} retries for {link}: {e}")
                            return (link, f"⚠️ Error scraping {link}: {e}")
                
                return (link, f"⚠️ Error scraping {link}: {last_error}")
            finally:
                await page.close()
        
        # Process pages concurrently with a limit
        max_concurrent = 30  # ⚡ OPTIMIZED: Maximum speed - 30 concurrent pages
        results = []
        
        for i in range(0, len(links), max_concurrent):
            batch = links[i:i+max_concurrent]
            batch_tasks = [scrape_page_task(link) for link in batch]
            batch_results = await asyncio.gather(*batch_tasks)
            results.extend(batch_results)
            # ⚡ OPTIMIZED: Removed delay for maximum speed
        
        # Order results by original link order
        for link, content in results:
            if content and len(content.strip()) > 50:  # Only include pages with substantial content
                ordered_results[link] = content
            else:
                logger.warning(f"Skipping {link} - insufficient content extracted")

    finally:
        await context.close()

    # Save results
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save JSON version
    json_filename = f"scraped_data/{section.replace('/', '_')}_{timestamp}.json"
    async with aiofiles.open(json_filename, "w", encoding="utf-8") as f:
        await f.write(json.dumps(ordered_results, ensure_ascii=False, indent=2))
    
    # Save Markdown version
    markdown_content = convert_to_markdown(ordered_results)
    md_filename = f"scraped_data/{section.replace('/', '_')}_{timestamp}.md"
    async with aiofiles.open(md_filename, "w", encoding="utf-8") as f:
        await f.write(markdown_content)
    
    logger.info(f"Saved {len(ordered_results)} pages to {json_filename} and {md_filename}")

    return ordered_results, json_filename


# --- External Services (Groq API - Optional) ---

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"

async def chunk_text(text: str, max_chunk_size: int = 10000) -> list:
    """Split text into chunks of specified size without breaking sentences"""
    if len(text) <= max_chunk_size:
        return [text]
    
    chunks = []
    paragraphs = text.split('\n\n')
    
    current_chunk = ""
    for paragraph in paragraphs:
        if len(current_chunk + paragraph) <= max_chunk_size:
            current_chunk += paragraph + "\n\n"
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            if len(paragraph) > max_chunk_size:
                sentences = paragraph.split('.')
                temp_chunk = ""
                for sentence in sentences:
                    sentence += '.'
                    if len(temp_chunk + sentence) <= max_chunk_size:
                        temp_chunk += sentence
                    else:
                        if temp_chunk:
                            chunks.append(temp_chunk.strip())
                            temp_chunk = sentence
                        else:
                            chunks.append(sentence.strip())
                            temp_chunk = ""
                if temp_chunk:
                    chunks.append(temp_chunk.strip())
            else:
                current_chunk = paragraph + "\n\n"
    
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    
    return chunks


# --- API Routes ---

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.datetime.now().isoformat(),
        "version": "2.0.0"
    }

@app.get("/api/list-scraped-data")
async def list_scraped_data():
    try:
        files = []
        for f in os.listdir("scraped_data"):
            if f.endswith(('.json', '.pdf', '.md')):
                file_path = os.path.join("scraped_data", f)
                file_stats = os.stat(file_path)
                files.append({
                    "filename": f,
                    "size": file_stats.st_size,
                    "modified": datetime.datetime.fromtimestamp(file_stats.st_mtime).isoformat()
                })
        return {"files": files}
    except Exception as e:
        logger.error(f"Error listing files: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing files: {str(e)}"
        )

@app.get("/api/get-scraped-data/{filename}")
async def get_scraped_data(filename: str):
    try:
        file_path = os.path.join("scraped_data", filename)
        if not os.path.exists(file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File {filename} not found"
            )

        async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
            if filename.endswith('.json'):
                data = json.loads(await f.read())
            else:
                data = await f.read()

        return {"filename": filename, "content": data}
    except Exception as e:
        logger.error(f"Error reading file: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error reading file: {str(e)}"
        )

@app.post("/api/scrape", response_model=ScrapeResponse)
async def scrape_endpoint(scrape_req: ScrapeRequest):
    try:
        url = str(scrape_req.url)
        
        # Robust URL parsing
        parsed_url = urlparse(url.rstrip('/'))
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        path_parts = [part for part in parsed_url.path.split('/') if part]
        
        if not path_parts:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="URL must include a section path (e.g., https://docs.example.com/section)"
            )
        
        # Handle multi-level paths
        section = '/'.join(path_parts)
        
        logger.info(f"Starting scrape - URL: {url}, Base: {base_url}, Section: {section}")

        # Scrape the section
        results, json_filename = await scrape_section(base_url, section)

        if not results:
            return ScrapeResponse(
                status="warning",
                message=f"No content could be extracted from {url}",
                pages_found=0,
                results=None,
                pdf_filename=None
            )

        return ScrapeResponse(
            status="success",
            message=f"Successfully scraped {len(results)} pages from {base_url}/{section}",
            pages_found=len(results),
            results=results,
            pdf_filename=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Scrape endpoint error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An internal error occurred: {str(e)}"
        )

@app.get("/api/download/{filename}")
async def download_file(filename: str):
    file_path = os.path.join("scraped_data", filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    if filename.endswith(".pdf"):
        media_type = "application/pdf"
    elif filename.endswith(".json"):
        media_type = "application/json"
    elif filename.endswith(".md"):
        media_type = "text/markdown"
    else:
        media_type = "application/octet-stream"
    
    return FileResponse(file_path, media_type=media_type, filename=filename)


# --- Main Entry Point ---
if __name__ == "__main__":
    import uvicorn
    
    print("\n" + "="*50)
    print("📚 Documentation Scraper API v2.0")
    print("="*50)
    print("\n✅ Server starting...")
    
    if not GROQ_API_KEY:
        print("⚠️  WARNING: GROQ_API_KEY not set (content enhancement disabled)")
    else:
        print("✅ GROQ API key loaded")
    
    print("\n📍 Access points:")
    print("   • API endpoint: http://localhost:5000")
    print("   • API documentation: http://localhost:5000/docs")
    print("   • Health check: http://localhost:5000/api/health")
    print("\n" + "="*50 + "\n")
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=5000,
        log_level="info"
    )