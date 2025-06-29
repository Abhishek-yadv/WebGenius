import asyncio
import datetime
import os
import aiofiles
from urllib.parse import urljoin
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from typing import Dict, Optional, List, Any
import json
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import logging
from contextlib import asynccontextmanager
import uuid

# Logging configuration for Cloud Run
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Models
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
        _browser = await playwright.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--no-first-run',
                '--no-zygote',
                '--single-process',
                '--disable-extensions'
            ]
        )
    return _browser

async def shutdown_browser():
    global _browser
    if _browser:
        await _browser.close()
        _browser = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting WebScraper API on Cloud Run")
    yield
    # Shutdown
    await shutdown_browser()
    logger.info("WebScraper API shutdown complete")

# FastAPI App
app = FastAPI(
    title="WebScraper Pro API",
    description="Professional web scraping API optimized for Google Cloud Run",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure data directory exists
os.makedirs("scraped_data", exist_ok=True)

# Extract content from a page
async def extract_content_from_page(page, url):
    try:
        logger.info(f"Extracting content from: {url}")
        await page.goto(url, timeout=45000, wait_until="domcontentloaded")
        await page.wait_for_selector("body", timeout=10000)

        content = await page.content()
        soup = BeautifulSoup(content, "html.parser")

        extracted_data = {
            "title": soup.find("title").get_text() if soup.find("title") else "Untitled Page",
            "description": "",
            "text": "",
            "links": [],
            "images": [],
            "metadata": {}
        }

        # Get description
        desc_tag = soup.find("meta", attrs={"name": "description"})
        if desc_tag and desc_tag.get("content"):
            extracted_data["description"] = desc_tag["content"]

        # Get main content
        main_content = (soup.find("main") or
                        soup.find("article") or
                        soup.find("div", class_=["content", "documentation"]) or
                        soup.body)

        if main_content:
            # Remove unwanted elements
            for unwanted in main_content.select("nav, aside, .sidebar, .menu"):
                unwanted.decompose()

            # Extract text
            text_parts = []
            for el in main_content.find_all(["h1", "h2", "h3", "h4", "p", "pre", "code", "li"]):
                if el.name == "pre":
                    text_parts.append("\n```\n" + el.get_text() + "\n```\n")
                elif el.name.startswith("h"):
                    level = int(el.name[1])
                    text_parts.append("\n" + "#" * level + " " + el.get_text())
                else:
                    text_parts.append(el.get_text())
            extracted_data["text"] = "\n\n".join(text_parts).strip()

            # Extract links
            for a_tag in main_content.find_all("a", href=True):
                href = urljoin(url, a_tag["href"])
                if href.startswith("http") and href not in extracted_data["links"]:
                    extracted_data["links"].append(href)
            
            # Extract images
            for img_tag in main_content.find_all("img", src=True):
                src = urljoin(url, img_tag["src"])
                if src.startswith("http") and src not in extracted_data["images"]:
                    extracted_data["images"].append(src)

        return extracted_data
    except Exception as e:
        logger.warning(f"Failed to extract content from {url}: {str(e)}")
        return {
            "title": "Error Page",
            "description": "",
            "text": f"Failed to load content from {url}: {str(e)}",
            "links": [],
            "images": [],
            "metadata": {},
            "error": str(e)
        }

# API Routes
@app.get("/")
async def root():
    return {
        "message": "WebScraper Pro API - Cloud Run Edition",
        "status": "online",
        "docs": "/docs",
        "platform": "Google Cloud Run"
    }

@app.post("/api/scrape", response_model=ScrapeResponse)
async def scrape_endpoint(scrape_req: ScrapeRequest):
    try:
        url = str(scrape_req.url)
        logger.info(f"Scraping request for URL: {url}")
        
        browser = await get_browser()
        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = await context.new_page()

        try:
            data = await extract_content_from_page(page, url)
            result = {
                "id": str(uuid.uuid4()),
                "url": url,
                "timestamp": datetime.datetime.now().isoformat(),
                "status": "completed" if "error" not in data else "error",
                "data": data,
                "error": data.get("error")
            }

            # Save to file
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"scraped_data/scrape_{timestamp}.json"
            async with aiofiles.open(filename, "w", encoding="utf-8") as f:
                await f.write(json.dumps([result], ensure_ascii=False, indent=2))

            return {
                "status": "success",
                "message": f"Successfully scraped {url}",
                "pages_found": 1,
                "results": [result]
            }
        finally:
            await context.close()

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
    return {
        "status": "healthy",
        "timestamp": datetime.datetime.now().isoformat(),
        "platform": "Google Cloud Run",
        "version": "1.0.0"
    }

# Cloud Run entry point
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"Starting WebScraper API on port {port}")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info",
        access_log=True
    )