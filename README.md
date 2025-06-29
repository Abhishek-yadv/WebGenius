# WebScraper Pro

A modern, full-stack web scraping application with a beautiful React frontend and powerful FastAPI backend.

## Features

### Frontend (React + TypeScript)
- 🎨 Modern glassmorphism design with dark/light themes
- 📱 Fully responsive interface
- 🔄 Real-time scraping progress tracking
- 📊 Comprehensive results display with statistics
- 💾 Export functionality (JSON, CSV, MD, PDF)
- 📝 Persistent scraping history
- ⚙️ Advanced scraping options and settings
- 🌐 API health monitoring

### Backend (FastAPI + Python)
- 🚀 High-performance async web scraping with Playwright
- 🔧 Configurable extraction options
- 📦 Documentation-focused scraping
- 💾 Automatic result storage
- 🛡️ Error handling and validation
- 📚 Auto-generated API documentation
- 🔄 CORS support for frontend integration

## Quick Start

### Prerequisites
- Node.js 16+ 
- Python 3.8+

### Installation

1. **Install frontend dependencies:**
   ```bash
   npm install
   ```

2. **Install backend dependencies:**
   ```bash
   npm run install-backend
   ```

### Running the Application

#### Development Mode

1. **Start the backend server:**
   ```bash
   npm run backend
   ```
   The API will be available at `http://localhost:5000`

2. **Start the frontend development server:**
   ```bash
   npm run dev
   ```
   The web interface will be available at `http://localhost:5173`

#### Production Deployment

##### Option 1: Render (Recommended)

**Backend Deployment:**
1. **Sign up at [Render](https://render.com)**
2. **Create a new Web Service**
3. **Connect your GitHub repository**
4. **Configure the service:**
   - **Build Command:** `pip install -r backend/requirements.txt && python -m playwright install chromium`
   - **Start Command:** `python backend/main.py`
   - **Environment Variables:**
     - `PORT`: 10000
     - `PYTHONPATH`: /opt/render/project/src

**Frontend Deployment:**
1. **Create another Web Service for the frontend**
2. **Configure the service:**
   - **Build Command:** `npm install && npm run build`
   - **Start Command:** `npm start`
   - **Environment Variables:**
     - `PORT`: 10000
     - `VITE_RENDER_BACKEND_URL`: `https://your-backend-service.onrender.com`

##### Option 2: Separate Deployments

**Frontend (Netlify):**
1. Build the project: `npm run build`
2. Deploy the `dist/` folder to Netlify
3. Set environment variable: `VITE_RENDER_BACKEND_URL=https://your-backend.onrender.com`

**Backend (Render):**
1. Deploy using the backend configuration above

##### Update Configuration
After deploying your backend:

1. **Copy `.env.example` to `.env`**
2. **Update the backend URL:**
   ```env
   VITE_RENDER_BACKEND_URL=https://your-actual-backend.onrender.com
   ```
3. **Redeploy your frontend**

## API Documentation

Once the backend is running, visit `http://localhost:5000/docs` for interactive API documentation.

### Key Endpoints

- `POST /api/scrape` - Scrape a documentation section
- `GET /api/list-scraped-data` - List all scraped data files
- `GET /api/get-scraped-data/{filename}` - Get specific scraped data
- `GET /api/health` - Health check endpoint

## Scraping Features

The scraper is specifically designed for documentation websites and supports:

- **Documentation Section Scraping**: Automatically discovers and scrapes all pages in a documentation section
- **Content Extraction**: Page title, description, and main content with sidebar removal
- **Link Discovery**: Finds all related documentation pages
- **Image Extraction**: Captures image URLs and sources
- **Metadata Collection**: Extracts meta tags and page metadata
- **DOM-Ordered Results**: Maintains the natural order of pages as they appear
- **Concurrent Processing**: Efficient batch processing with rate limiting

## Data Storage

Scraped data is automatically saved to the `scraped_data/` directory in JSON format with timestamps.

## Architecture

### Frontend Stack
- **React 18** with TypeScript
- **Tailwind CSS** for styling
- **Lucide React** for icons
- **Vite** for development and building

### Backend Stack
- **FastAPI** for the web framework
- **Playwright** for web scraping and browser automation
- **BeautifulSoup4** for HTML parsing
- **Pydantic** for data validation
- **Uvicorn** for the ASGI server

## Development

### Frontend Development
```bash
npm run dev        # Start development server
npm run build      # Build for production
npm run lint       # Run ESLint
npm start          # Start production preview server
```

### Backend Development
```bash
npm run backend    # Start backend with auto-reload
```

## Deployment Architecture

```
Frontend (Render/Netlify) ←→ Backend (Render)
     ↓                           ↓
Static Files/Node.js        Python + FastAPI
React SPA                   Playwright Scraper
                           Data Storage
```

## Environment Variables

### Development
- Automatically uses `localhost:5000` for API calls

### Production
- `VITE_RENDER_BACKEND_URL` - Your backend service URL
- `PORT` - Server port (automatically set by hosting providers)

## Troubleshooting

### Render Deployment Issues
1. **Build fails**: Check that dependencies are correctly specified
2. **Playwright issues**: Ensure Chromium is installed in build command
3. **Port issues**: Render automatically sets PORT environment variable
4. **Memory issues**: Consider upgrading to a paid Render plan for better performance

### Frontend Connection Issues
1. **CORS errors**: Backend is configured to allow all origins
2. **API offline**: Check that your backend service is running
3. **Wrong URL**: Verify `VITE_RENDER_BACKEND_URL` in your environment variables

### Common Deployment Errors
- **"Command not found"**: Make sure `start` script is defined in package.json
- **Build failures**: Check that all dependencies are listed in package.json
- **Environment variables**: Ensure all required env vars are set in your hosting platform

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

MIT License - see LICENSE file for details.