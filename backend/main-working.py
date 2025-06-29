import asyncio
import datetime
import os
import aiofiles
from urllib.parse import urljoin
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Optional, List, Any
import json
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import logging
from contextlib import asynccontextmanager
from collections import OrderedDict
import uuid

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global Playwright browser instance
_browser = None

async def get_browser():
    global _browser
    if _browser is None:
        playwright = await async_playwright().start()
        _browser = await playwright.chromium.launch(headless=True)
    return _browser

async def shutdown_browser():
    global _browser
    if _browser:
        await _browser.close()
        _browser = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await shutdown_browser()

# FastAPI App
app = FastAPI(
    title="Documentation Scraper API",
    description="An API to scrape and process documentation websites",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("scraped_data", exist_ok=True)

# ✅ Extract links in DOM order (not sorted)
async def extract_links_from_section(page, section_url, section_prefix):
    logger.info(f"Navigating to section: {section_url}")
    try:
        await page.goto(section_url, timeout=45000, wait_until="domcontentloaded")
        await page.wait_for_selector("body", timeout=10000)
    except Exception as e:
        logger.warning(f"Error navigating to {section_url}: {str(e)}")
        return []

    links = []
    seen = set()

    elements = await page.query_selector_all('a[href]')
    for element in elements:
        href = await element.get_attribute('href')
        if not href:
            continue
        full_url = urljoin(section_url, href)
        if (f"/{section_prefix}/" in full_url and
                full_url.startswith(section_url) and
                full_url not in seen):
            links.append(full_url)
            seen.add(full_url)

    return links

# ✅ Extract main content from a page with sidebar removal
async def extract_content_from_page(page, url):
    try:
        logger.info(f"Extracting content from: {url}")
        await page.goto(url, timeout=45000, wait_until="domcontentloaded")
        try:
            await page.wait_for_selector("main, article, div.content, div.documentation, body", timeout=10000)
        except:
            await page.wait_for_selector("body", timeout=5000)

        content = await page.content()
        # FIXED: Use html.parser instead of lxml to avoid C++ compilation
        soup = BeautifulSoup(content, "html.parser")

        main_content = (soup.find("main") or
                        soup.find("article") or
                        soup.find("div", class_=["content", "documentation"]) or
                        soup.body)

        if not main_content:
            return "No content found"

        # ✅ Remove sidebar, nav, and other non-content sections
        for unwanted in main_content.select(".sidebar, #sidebar, nav, aside, [class*=sidebar], [id*=sidebar], [class*=navigation], .toc, .menu"):
            unwanted.decompose()

        title = soup.find("title")
        title_text = title.get_text() if title else "Untitled Page"
        text_parts = [f"# {title_text}"]

        for el in main_content.find_all(["h1", "h2", "h3", "h4", "p", "pre", "code", "li", "blockquote"]):
            if el.name == "pre":
                text_parts.append("\n```\n" + el.get_text() + "\n```\n")
            elif el.name.startswith("h"):
                level = int(el.name[1])
                text_parts.append("\n" + "#" * level + " " + el.get_text())
            else:
                text_parts.append(el.get_text())

        return "\n\n".join(text_parts).strip()
    except Exception as e:
        logger.warning(f"Failed to load {url}: {str(e)}")
        return f"⚠️ Failed to load {url}: {str(e)}"

# ✅ Scrape section with DOM-ordered results
async def scrape_section(base_url, section):
    section_url = f"{base_url}/{section}"
    ordered_results = OrderedDict()

    browser = await get_browser()
    context = await browser.new_context(
        viewport={"width": 1280, "height": 800},
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
        extra_http_headers={"Accept": "text/html,application/xhtml+xml"},
        java_script_enabled=False
    )
    page = await context.new_page()

    links = await extract_links_from_section(page, section_url, section)
    logger.info(f"Found {len(links)} page(s) under section /{section}")

    if not links:
        links = [section_url]

    async def scrape_page(index, link):
        page = await context.new_page()
        try:
            content = await extract_content_from_page(page, link)
            return index, link, content
        except Exception as e:
            logger.warning(f"Error scraping {link}: {e}")
            return index, link, f"⚠️ Error scraping {link}: {e}"
        finally:
            await page.close()

    max_concurrent = 5
    tasks = [scrape_page(i, link) for i, link in enumerate(links)]
    for i in range(0, len(tasks), max_concurrent):
        batch = tasks[i:i + max_concurrent]
        results = await asyncio.gather(*batch, return_exceptions=False)
        for index, link, content in results:
            ordered_results[link] = content

    await context.close()

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"scraped_data/{section}_{timestamp}.json"
    async with aiofiles.open(filename, "w", encoding="utf-8") as f:
        await f.write(json.dumps(ordered_results, ensure_ascii=False, indent=2))

    return ordered_results, filename

# API Routes
@app.get("/")
async def root():
    return {"message": "WebScraper Pro API", "status": "online", "docs": "/docs"}

@app.post("/api/scrape")
async def scrape_endpoint(request_data: dict):
    try:
        url = request_data.get("url")
        if not url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="URL is required"
            )
        
        parts = url.rstrip('/').split('/')
        base_url = '/'.join(parts[:3])
        section = parts[3] if len(parts) > 3 else ''
        logger.info(f"Scraping URL: {url}, Base: {base_url}, Section: {section}")

        if not section:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="URL must include a section path (e.g., https://docs.example.com/section)"
            )

        results, filename = await scrape_section(base_url, section)

        return {
            "status": "success",
            "message": f"Successfully scraped {len(results)} pages from {base_url}/{section}",
            "pages_found": len(results),
            "results": results
        }
    except Exception as e:
        logger.error(f"Scrape error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error during scraping: {str(e)}"
        )

@app.get("/api/list-scraped-data")
async def list_scraped_data():
    try:
        files = os.listdir("scraped_data")
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
            data = json.loads(await f.read())

        return data
    except Exception as e:
        logger.error(f"Error reading file: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error reading file: {str(e)}"
        )

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.datetime.now().isoformat()}

# Dev server entry
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 5000))
    print("\n===== Documentation Scraper API =====")
    print("Starting server...")
    print("Access the API via:")
    print("• http://localhost:5000/")
    print("• API documentation: http://localhost:5000/docs")
    print("=======================================\n")
    uvicorn.run(app, host="0.0.0.0", port=port)