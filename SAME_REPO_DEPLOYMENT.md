# Deploy Backend from Same Repository

## Quick Steps:

### 1. Create New Web Service for Backend
1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click **"New +" → "Web Service"**
3. **Connect the SAME GitHub repository** you used for frontend

### 2. Configure Backend Service
When setting up the new service, use these settings:

**Basic Info:**
- **Name**: `webscraper-backend` (different from your frontend service name)
- **Environment**: `Python` (NOT Node)
- **Region**: Same as your frontend
- **Branch**: `main`

**Build & Deploy:**
- **Build Command**: 
  ```
  pip install -r backend/requirements.txt && python -m playwright install chromium
  ```
- **Start Command**: 
  ```
  python backend/main.py
  ```

**Environment Variables:**
- `PORT`: `10000` (Render sets automatically)
- `PYTHONPATH`: `/opt/render/project/src`

### 3. Deploy Backend
- Click **"Create Web Service"**
- Wait 5-10 minutes for deployment (Playwright takes time to install)
- Note your backend URL: `https://webscraper-backend-[random].onrender.com`

### 4. Update Frontend Service
1. Go to your existing frontend service in Render
2. Go to **Environment** tab
3. Add environment variable:
   - **Key**: `VITE_RENDER_BACKEND_URL`
   - **Value**: `https://your-backend-service-url.onrender.com`
4. **Manual Deploy** to update frontend

## Why This Works:
- **Same Repository**: Both services use the same GitHub repo
- **Different Configurations**: Frontend uses Node.js, Backend uses Python
- **Different Start Commands**: Frontend serves React app, Backend runs FastAPI
- **Separate Services**: Each has its own URL and resources

## Result:
- **Frontend**: `https://webgenius-6nph.onrender.com` (your existing service)
- **Backend**: `https://webscraper-backend-xyz.onrender.com` (new service)
- **Communication**: Frontend calls backend API for scraping

## Testing:
Once both are deployed, test:
1. Visit your frontend URL
2. Try scraping a website
3. Check if API status shows "Online"