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

##### Frontend (Netlify)
The frontend is already configured for Netlify deployment:

1. Build the project: `npm run build`
2. Deploy the `dist/` folder to Netlify
3. The frontend will automatically detect if it's in production mode

##### Backend (Render)
The backend is configured for Render deployment:

1. **Sign up at [Render](https://render.com)**
2. **Create a new Web Service**
3. **Connect your GitHub repository**
4. **Render will automatically detect the configuration:**
   - Uses `render.yaml` for configuration
   - Installs Python dependencies from `backend/requirements.txt`
   - Installs Playwright Chromium browser
   - Starts the server with `python main.py`
5. **Deploy and get your backend URL**

##### Alternative: Manual Render Setup
If automatic detection doesn't work:

1. **Build Command:** `cd backend && pip install -r requirements.txt && python -m playwright install chromium`
2. **Start Command:** `cd backend && python main.py`
3. **Environment Variables:**
   - `PORT`: 10000 (Render default)
   - `PYTHONPATH`: /opt/render/project/src/backend

##### Update Frontend Configuration
After deploying your backend to Render:

1. **Copy `.env.example` to `.env`**
2. **Update the Render backend URL:**
   ```env
   VITE_RENDER_BACKEND_URL=https://your-actual-app.onrender.com
   ```
3. **Redeploy your frontend to Netlify**

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
```

### Backend Development
```bash
npm run backend    # Start backend with auto-reload
```

## Deployment Architecture

```
Frontend (Netlify) ←→ Backend (Render)
     ↓                      ↓
Static Files          Python + FastAPI
React SPA            Playwright Scraper
                     Data Storage
```

## Environment Variables

### Development
- Automatically uses `localhost:5000` for API calls

### Production
- `VITE_RENDER_BACKEND_URL` - Your Render backend URL

## Troubleshooting

### Render Deployment Issues
1. **Build fails**: Check that `render.yaml` is in the root directory
2. **Playwright issues**: Ensure Chromium is installed in build command
3. **Port issues**: Render uses port 10000 by default, our app adapts automatically
4. **Memory issues**: Consider upgrading to a paid Render plan for better performance

### Frontend Connection Issues
1. **CORS errors**: Backend is configured to allow all origins
2. **API offline**: Check that your Render service is running
3. **Wrong URL**: Verify `VITE_RENDER_BACKEND_URL` in your `.env` file

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

MIT License - see LICENSE file for details.