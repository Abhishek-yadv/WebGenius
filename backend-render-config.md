# Backend Deployment Configuration for Render

## Service Settings
- **Name**: `webscraper-backend` (or any name you prefer)
- **Environment**: `Python`
- **Region**: `Oregon` (or your preferred region)
- **Branch**: `main`
- **Root Directory**: Leave empty (uses repository root)

## Build & Deploy Settings
- **Build Command**: 
  ```bash
  pip install -r backend/requirements.txt && python -m playwright install chromium
  ```

- **Start Command**: 
  ```bash
  python backend/main.py
  ```

## Environment Variables
Add these in the Render dashboard:
- `PORT`: `10000` (Render will set this automatically)
- `PYTHONPATH`: `/opt/render/project/src`

## Health Check
- **Health Check Path**: `/api/health`

## Expected Deployment URL
Your backend will be available at something like:
`https://webscraper-backend-[random].onrender.com`