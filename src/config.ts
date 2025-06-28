// Configuration for API endpoints
const isDevelopment = import.meta.env.DEV;
const RAILWAY_BACKEND_URL = import.meta.env.VITE_RAILWAY_BACKEND_URL;

export const API_BASE_URL = isDevelopment 
  ? 'http://localhost:5000' 
  : RAILWAY_BACKEND_URL || 'https://your-app.railway.app'; // Replace with your actual Railway URL

export const config = {
  apiBaseUrl: API_BASE_URL,
  isDevelopment,
};