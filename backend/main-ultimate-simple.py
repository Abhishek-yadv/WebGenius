import asyncio
import datetime
import os
import json
from urllib.parse import urljoin
from http.server import HTTPServer, BaseHTTPRequestHandler
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import logging
import uuid
import threading

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global Playwright browser instance
_browser = None
_playwright = None

async def get_browser():
    global _browser, _playwright
    if _browser is None:
        _playwright = await async_playwright().start()
        _browser = await _playwright.chromium.launch(headless=True)
    return _browser

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
        main_content = soup.find("main") or soup.find("article") or soup.find("div", class_="content") or soup.body

        if main_content:
            # Remove unwanted elements
            for unwanted in main_content.find_all(["nav", "aside"]):
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

def run_async(coro):
    """Run async function in sync context"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

class APIHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        """Handle GET requests"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        if self.path == '/':
            response = {"message": "WebScraper Pro API", "status": "online", "docs": "/docs"}
        elif self.path == '/api/health':
            response = {"status": "healthy", "timestamp": datetime.datetime.now().isoformat()}
        elif self.path == '/docs':
            response = {
                "title": "WebScraper Pro API Documentation",
                "version": "1.0.0",
                "endpoints": {
                    "GET /": "API status and info",
                    "POST /api/scrape": "Scrape a website URL",
                    "GET /api/health": "Health check endpoint",
                    "GET /docs": "This documentation"
                }
            }
        else:
            response = {"error": "Not found"}
        
        self.wfile.write(json.dumps(response).encode())

    def do_POST(self):
        """Handle POST requests"""
        if self.path == '/api/scrape':
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
                
                url = data.get("url")
                if not url:
                    self.send_error(400, "URL is required")
                    return
                
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
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(result).encode())
                
            except Exception as e:
                logger.error(f"Scrape error: {str(e)}")
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                error_response = {"error": f"Error during scraping: {str(e)}"}
                self.wfile.write(json.dumps(error_response).encode())
        else:
            self.send_error(404, "Not found")

    def log_message(self, format, *args):
        """Override to use our logger"""
        logger.info(f"{self.address_string()} - {format % args}")

def run_server():
    port = int(os.environ.get("PORT", 5000))
    server = HTTPServer(('0.0.0.0', port), APIHandler)
    
    print(f"\n===== Documentation Scraper API =====")
    print(f"Starting HTTP server on port {port}...")
    print(f"Access the API via:")
    print(f"• http://localhost:{port}/")
    print(f"• API documentation: http://localhost:{port}/docs")
    print("=======================================\n")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.shutdown()

if __name__ == "__main__":
    run_server()