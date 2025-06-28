# WebScraper Pro

A modern, full-stack web scraping application with a beautiful React frontend and powerful FastAPI backend.

## Features

### Frontend (React + TypeScript)
- 🎨 Modern glassmorphism design with dark/light themes
- 📱 Fully responsive interface
- 🔄 Real-time scraping progress tracking
- 📊 Comprehensive results display with statistics
- 💾 Export functionality (JSON, CSV)
- 📝 Persistent scraping history
- ⚙️ Advanced scraping options and settings
- 🌐 API health monitoring

### Backend (FastAPI + Python)
- 🚀 High-performance async web scraping
- 🔧 Configurable extraction options
- 📦 Batch URL processing
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
   python -m pip install -r backend/requirements.txt
   ```

### Running the Application

1. **Start the backend server:**
   ```bash
   npm run backend
   # or directly: python backend/main.py
   ```
   The API will be available at `http://localhost:8000`

2. **Start the frontend development server:**
   ```bash
   npm run dev
   ```
   The web interface will be available at `http://localhost:5173`

## API Documentation

Once the backend is running, visit `http://localhost:8000/docs` for interactive API documentation.

### Key Endpoints

- `POST /api/scrape` - Scrape a single URL
- `POST /api/batch-scrape` - Scrape multiple URLs
- `GET /api/scraped-data` - List all scraped data files
- `GET /api/scraped-data/{filename}` - Get specific scraped data
- `GET /api/health` - Health check endpoint

## Scraping Options

The scraper supports various extraction options:

- **Extract Text**: Page title, description, and main content
- **Extract Links**: All hyperlinks found on the page
- **Extract Images**: Image URLs and sources
- **Extract Metadata**: Meta tags and page metadata
- **Follow Redirects**: Handle URL redirections
- **Timeout**: Configurable request timeout

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
- **Pydantic** for data validation
- **Python standard library** for web scraping (urllib, html.parser)
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
python backend/main.py  # Start with auto-reload
```

## Production Deployment

### Frontend
```bash
npm run build
# Deploy the dist/ folder to your static hosting service
```

### Backend
```bash
# Install production dependencies
python -m pip install -r backend/requirements.txt

# Run with production settings
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

MIT License - see LICENSE file for details.