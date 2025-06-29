import asyncio
import datetime
import os
import aiofiles
from urllib.parse import urljoin
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Optional, List, Any
import json
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import logging
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

# FastAPI App - Ancient version, no lifespan support
app = FastAPI(
    title="Documentation Scraper API",
    description="An API to scrape and process documentation websites",
    version="1.0.0"
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

# Extract content from a page
async def extract_content_from_page(page, url):
    try:
        logger.info(f"Extracting content from: {url}")
        await page.goto(url, timeout=30000, wait_until="domcontentloaded")
        await page.wait_for_selector("body", timeout=5000)

        content = await page.content()
        soup = BeautifulSoup(content, "html.parser")

        extracted_data = {
            "title": "",
            "description": "",
            "text": "",
            "links": [],
            "images": [],
            "metadata": {}
        }

        # Get title
        title_tag = soup.find("title")
        if title_tag:
            extracted_data["title"] = title_tag.get_text().strip()
        else:
            extracted_data["title"] = "Untitled Page"

        # Get description
        desc_tag = soup.find("meta", attrs={"name": "description"})
        if desc_tag and desc_tag.get("content"):
            extracted_data["description"] = desc_tag["content"]

        # Get main content
        main_content = soup.find("main")
        if not main_content:
            main_content = soup.find("article")
        if not main_content:
            main_content = soup.find("div", class_="content")
        if not main_content:
            main_content = soup.body

        if main_content:
            # Remove unwanted elements
            for unwanted in main_content.find_all(["nav", "aside"]):
                unwanted.decompose()
            
            for unwanted in main_content.find_all("div", class_=["sidebar", "menu"]):
                unwanted.decompose()

            # Extract text
            text_parts = []
            for el in main_content.find_all(["h1", "h2", "h3", "h4", "p", "pre", "code", "li"]):
                text = el.get_text().strip()
                if text:
                    if el.name == "pre":
                        text_parts.append(f"\n```\n{text}\n```\n")
                    elif el.name.startswith("h"):
                        level = int(el.name[1])
                        text_parts.append(f"\n{'#' * level} {text}")
                    else:
                        text_parts.append(text)
            
            extracted_data["text"] = "\n\n".join(text_parts).strip()

            # Extract links
            for a_tag in main_content.find_all("a", href=True):
                href = a_tag["href"]
                if href:
                    full_url = urljoin(url, href)
                    if full_url.startswith("http") and full_url not in extracted_data["links"]:
                        extracted_data["links"].append(full_url)
            
            # Extract images
            for img_tag in main_content.find_all("img", src=True):
                src = img_tag["src"]
                if src:
                    full_url = urljoin(url, src)
                    if full_url.startswith("http") and full_url not in extracted_data["images"]:
                        extracted_data["images"].append(full_url)

        # Extract metadata
        for meta_tag in soup.find_all("meta"):
            name = meta_tag.get("name")
            content = meta_tag.get("content")
            if name and content:
                extracted_data["metadata"][name] = content
            
            prop = meta_tag.get("property")
            if prop and content:
                extracted_data["metadata"][prop] = content

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
    return {"message": "WebScraper Pro API", "status": "online", "docs": "/docs"}

@app.post("/api/scrape")
async def scrape_endpoint(request_data: dict):
    try:
        url = request_data.get("url")
        if not url:
            raise HTTPException(status_code=400, detail="URL is required")
        
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
        raise HTTPException(status_code=500, detail=f"Error during scraping: {str(e)}")

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.datetime.now().isoformat()}

# Startup/shutdown events for older FastAPI
@app.on_event("shutdown")
async def shutdown_event():
    await shutdown_browser()

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