# Backend Deployment Guide for Render

## Step 1: Create a New Web Service for Backend

1. **Go to [Render Dashboard](https://dashboard.render.com/)**
2. **Click "New +" → "Web Service"**
3. **Connect your GitHub repository** (same repo as frontend)

## Step 2: Configure the Backend Service

### Basic Settings:
- **Name**: `webscraper-backend` (or any name you prefer)
- **Environment**: `Python`
- **Region**: `Oregon` (or your preferred region)
- **Branch**: `main`
- **Root Directory**: Leave empty

### Build & Deploy Settings:
- **Build Command**: 
  ```bash
  pip install -r backend/requirements.txt && python -m playwright install chromium
  ```

- **Start Command**: 
  ```bash
  python backend/main.py
  ```

### Environment Variables:
Add these in the Render dashboard:
- `PORT`: `10000` (Render sets this automatically)
- `PYTHONPATH`: `/opt/render/project/src`

### Advanced Settings:
- **Health Check Path**: `/api/health`
- **Auto-Deploy**: `Yes` (recommended)

## Step 3: Deploy the Backend

1. **Click "Create Web Service"**
2. **Wait for deployment** (this may take 5-10 minutes due to Playwright installation)
3. **Note your backend URL** (will be something like `https://webscraper-backend-xyz.onrender.com`)

## Step 4: Update Frontend Configuration

Once your backend is deployed, you'll need to update your frontend to use the new backend URL:

1. **Get your backend URL** from the Render dashboard
2. **Update the frontend environment variable**:
   - If using Render for frontend: Set `VITE_RENDER_BACKEND_URL` to your backend URL
   - If using Netlify: Update the environment variable in Netlify dashboard

## Step 5: Redeploy Frontend

After updating the backend URL, redeploy your frontend service to pick up the new configuration.

## Expected URLs:
- **Backend API**: `https://webscraper-backend-[random].onrender.com`
- **API Documentation**: `https://webscraper-backend-[random].onrender.com/docs`
- **Health Check**: `https://webscraper-backend-[random].onrender.com/api/health`

## Troubleshooting:

### Common Issues:
1. **Build fails**: Check that `backend/requirements.txt` exists and is accessible
2. **Playwright installation fails**: This is normal on first deploy, may need to retry
3. **Service won't start**: Check logs for Python errors
4. **CORS issues**: Backend is configured to allow all origins

### Checking Logs:
- Go to your service in Render dashboard
- Click on "Logs" tab to see build and runtime logs
- Look for any error messages during startup

### Testing the Backend:
Once deployed, test these endpoints:
- `GET /api/health` - Should return health status
- `GET /docs` - Should show API documentation
- `POST /api/scrape` - Should accept scraping requests

## Performance Notes:
- **Free tier limitations**: 750 hours/month, sleeps after 15 minutes of inactivity
- **Cold starts**: First request after sleep may take 30+ seconds
- **Memory limits**: 512MB RAM on free tier
- **Consider upgrading** to paid plan for production use