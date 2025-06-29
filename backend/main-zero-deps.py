import datetime
import os
import json
from urllib.parse import urljoin
from http.server import HTTPServer, BaseHTTPRequestHandler
import requests
from bs4 import BeautifulSoup
import logging
import uuid

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

os.makedirs("scraped_data", exist_ok=True)

# Extract content from a page using requests
def extract_content_from_page(url):
    try:
        logger.info(f"Extracting content from: {url}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, "html.parser")

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
            for unwanted in main_content.find_all(["nav", "aside", "header", "footer"]):
                unwanted.decompose()
            
            for unwanted in main_content.find_all("div", class_=["sidebar", "menu", "navigation"]):
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
                },
                "note": "Using requests-based scraping for maximum compatibility"
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
                
                extracted_data = extract_content_from_page(url)
                result = {
                    "id": str(uuid.uuid4()),
                    "url": url,
                    "timestamp": datetime.datetime.now().isoformat(),
                    "status": "completed" if "error" not in extracted_data else "error",
                    "data": extracted_data,
                    "error": extracted_data.get("error")
                }

                response_data = {
                    "status": "success",
                    "message": f"Successfully scraped {url}",
                    "pages_found": 1,
                    "results": [result]
                }
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(response_data).encode())
                
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
    print("• Health check: http://localhost:{port}/api/health")
    print("=======================================\n")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.shutdown()

if __name__ == "__main__":
    run_server()