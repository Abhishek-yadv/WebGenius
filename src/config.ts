// Configuration for API endpoints
const isDevelopment = import.meta.env.DEV;
const RENDER_BACKEND_URL = import.meta.env.VITE_RENDER_BACKEND_URL;

export const API_BASE_URL = isDevelopment 
  ? 'http://localhost:5000' 
  : RENDER_BACKEND_URL || 'https://your-app.onrender.com'; // Replace with your actual Render URL

export const config = {
  apiBaseUrl: API_BASE_URL,
  isDevelopment,
};