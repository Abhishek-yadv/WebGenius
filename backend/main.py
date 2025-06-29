import asyncio
import datetime
import os
import aiofiles
from urllib.parse import urljoin
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, HttpUrl
from typing import Dict, Optional, List, Any
import json
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import logging
from contextlib import asynccontextmanager
import uuid

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Models - Updated for Pydantic v1 compatibility
class ScrapeRequest(BaseModel):
    url: HttpUrl

class ScrapeResponse(BaseModel):
    status: str
    message: str
    pages_found: int
    results: Optional[List[Dict[str, Any]]] = None

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
        soup = BeautifulSoup(content, "html.parser")

        extracted_data = {
            "title": soup.find("title").get_text() if soup.find("title") else "Untitled Page",
            "description": soup.find("meta", attrs={"name": "description"})["content"] if soup.find("meta", attrs={"name": "description"}) else "",
            "text": "",
            "links": [],
            "images": [],
            "metadata": {}
        }

        main_content = (soup.find("main") or
                        soup.find("article") or
                        soup.find("div", class_=["content", "documentation"]) or
                        soup.body)

        if not main_content:
            extracted_data["text"] = "No content found"
            return extracted_data

        # Remove sidebar, nav, and other non-content sections
        for unwanted in main_content.select(".sidebar, #sidebar, nav, aside, [class*=sidebar], [id*=sidebar], [class*=navigation], .toc, .menu"):
            unwanted.decompose()

        text_parts = []
        for el in main_content.find_all(["h1", "h2", "h3", "h4", "p", "pre", "code", "li", "blockquote"]):
            if el.name == "pre":
                text_parts.append("\n```\n" + el.get_text() + "\n```\n")
            elif el.name.startswith("h"):
                level = int(el.name[1])
                text_parts.append("\n" + "#" * level + " " + el.get_text())
            else:
                text_parts.append(el.get_text())
        extracted_data["text"] = "\n\n".join(text_parts).strip()

        for a_tag in main_content.find_all("a", href=True):
            href = urljoin(url, a_tag["href"])
            if href.startswith("http") and href not in extracted_data["links"]:
                extracted_data["links"].append(href)
        
        for img_tag in main_content.find_all("img", src=True):
            src = urljoin(url, img_tag["src"])
            if src.startswith("http") and src not in extracted_data["images"]:
                extracted_data["images"].append(src)

        # Basic metadata extraction (can be expanded)
        for meta_tag in soup.find_all("meta"):
            if meta_tag.get("name") and meta_tag.get("content"):
                extracted_data["metadata"][meta_tag["name"]] = meta_tag["content"]
            elif meta_tag.get("property") and meta_tag.get("content"):
                extracted_data["metadata"][meta_tag["property"]] = meta_tag["content"]

        return extracted_data
    except Exception as e:
        logger.warning(f"Failed to load or extract content from {url}: {str(e)}")
        return {
            "title": "Error Page",
            "description": "",
            "text": f"⚠️ Failed to load or extract content from {url}: {str(e)}",
            "links": [],
            "images": [],
            "metadata": {},
            "error": str(e)
        }

# ✅ Scrape section with DOM-ordered results
async def scrape_section(base_url, section):
    section_url = f"{base_url}/{section}"
    scraped_results_list = []

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

    async def scrape_page_task(link):
        page = await context.new_page()
        try:
            data = await extract_content_from_page(page, link)
            return {
                "id": str(uuid.uuid4()), # Generate a unique ID for each result
                "url": link,
                "timestamp": datetime.datetime.now().isoformat(),
                "status": "completed" if "error" not in data else "error",
                "data": data,
                "error": data.get("error")
            }
        except Exception as e:
            logger.warning(f"Error scraping {link}: {e}")
            return {
                "id": str(uuid.uuid4()),
                "url": link,
                "timestamp": datetime.datetime.now().isoformat(),
                "status": "error",
                "data": {},
                "error": str(e)
            }
        finally:
            await page.close()

    max_concurrent = 5
    tasks = [scrape_page_task(link) for link in links]
    for i in range(0, len(tasks), max_concurrent):
        batch = tasks[i:i + max_concurrent]
        results_batch = await asyncio.gather(*batch, return_exceptions=False)
        scraped_results_list.extend(results_batch)

    await context.close()

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"scraped_data/{section}_{timestamp}.json"
    async with aiofiles.open(filename, "w", encoding="utf-8") as f:
        await f.write(json.dumps(scraped_results_list, ensure_ascii=False, indent=2))

    return scraped_results_list, filename

# API Routes
@app.get("/")
async def root():
    return {"message": "WebScraper Pro API", "status": "online", "docs": "/docs"}

@app.post("/api/scrape", response_model=ScrapeResponse)
async def scrape_endpoint(scrape_req: ScrapeRequest):
    try:
        url = str(scrape_req.url)
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
    print(f"\n===== Documentation Scraper API =====")
    print(f"Starting server on port {port}...")
    print(f"Access the API via:")
    print(f"• http://localhost:{port}/")
    print(f"• API documentation: http://localhost:{port}/docs")
    print("=======================================\n")
    uvicorn.run(app, host="0.0.0.0", port=port)