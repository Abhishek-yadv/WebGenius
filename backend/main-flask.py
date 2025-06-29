import asyncio
import datetime
import os
import json
from urllib.parse import urljoin
from flask import Flask, request, jsonify
from flask_cors import CORS
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import logging
import uuid
import threading
from concurrent.futures import ThreadPoolExecutor

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask App
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Global Playwright browser instance
_browser = None
_playwright = None

def get_event_loop():
    """Get or create event loop for the current thread"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            raise RuntimeError("Event loop is closed")
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop

async def get_browser():
    global _browser, _playwright
    if _browser is None:
        _playwright = await async_playwright().start()
        _browser = await _playwright.chromium.launch(headless=True)
    return _browser

async def shutdown_browser():
    global _browser, _playwright
    if _browser:
        await _browser.close()
        _browser = None
    if _playwright:
        await _playwright.stop()
        _playwright = None

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

def run_async(coro):
    """Run async function in sync context"""
    loop = get_event_loop()
    if loop.is_running():
        # If loop is already running, use thread executor
        with ThreadPoolExecutor() as executor:
            future = executor.submit(asyncio.run, coro)
            return future.result()
    else:
        return loop.run_until_complete(coro)

# API Routes
@app.route('/')
def root():
    return jsonify({"message": "WebScraper Pro API", "status": "online", "docs": "/docs"})

@app.route('/api/scrape', methods=['POST'])
def scrape_endpoint():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
            
        url = data.get("url")
        if not url:
            return jsonify({"error": "URL is required"}), 400
        
        async def scrape_async():
            browser = await get_browser()
            context = await browser.new_context(
                viewport={"width": 1280, "height": 800},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            page = await context.new_page()

            try:
                extracted_data = await extract_content_from_page(page, url)
                result = {
                    "id": str(uuid.uuid4()),
                    "url": url,
                    "timestamp": datetime.datetime.now().isoformat(),
                    "status": "completed" if "error" not in extracted_data else "error",
                    "data": extracted_data,
                    "error": extracted_data.get("error")
                }

                return {
                    "status": "success",
                    "message": f"Successfully scraped {url}",
                    "pages_found": 1,
                    "results": [result]
                }
            finally:
                await context.close()

        result = run_async(scrape_async())
        return jsonify(result)

    except Exception as e:
        logger.error(f"Scrape error: {str(e)}")
        return jsonify({"error": f"Error during scraping: {str(e)}"}), 500

@app.route('/api/health')
def health_check():
    return jsonify({"status": "healthy", "timestamp": datetime.datetime.now().isoformat()})

@app.route('/docs')
def docs():
    return jsonify({
        "title": "WebScraper Pro API Documentation",
        "version": "1.0.0",
        "endpoints": {
            "GET /": "API status and info",
            "POST /api/scrape": "Scrape a website URL",
            "GET /api/health": "Health check endpoint",
            "GET /docs": "This documentation"
        },
        "scrape_endpoint": {
            "method": "POST",
            "url": "/api/scrape",
            "body": {
                "url": "https://example.com"
            },
            "response": {
                "status": "success",
                "message": "Successfully scraped URL",
                "pages_found": 1,
                "results": [
                    {
                        "id": "unique-id",
                        "url": "scraped-url",
                        "timestamp": "ISO-timestamp",
                        "status": "completed",
                        "data": {
                            "title": "Page title",
                            "description": "Page description",
                            "text": "Extracted text content",
                            "links": ["array", "of", "links"],
                            "images": ["array", "of", "images"],
                            "metadata": {"key": "value"}
                        }
                    }
                ]
            }
        }
    })

# Dev server entry
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"\n===== Documentation Scraper API =====")
    print(f"Starting Flask server on port {port}...")
    print(f"Access the API via:")
    print(f"• http://localhost:{port}/")
    print(f"• API documentation: http://localhost:{port}/docs")
    print("=======================================\n")
    
    # Install flask-cors if not available
    try:
        from flask_cors import CORS
    except ImportError:
        print("Installing flask-cors...")
        os.system("pip install flask-cors")
        from flask_cors import CORS
        CORS(app)
    
    app.run(host="0.0.0.0", port=port, debug=False)