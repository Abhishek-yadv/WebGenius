// Configuration for API endpoints
const isDevelopment = import.meta.env.DEV;
const RENDER_BACKEND_URL = import.meta.env.VITE_RENDER_BACKEND_URL;

// Update this with your actual backend URL once deployed
export const API_BASE_URL = isDevelopment 
  ? 'http://localhost:5000' 
  : RENDER_BACKEND_URL || 'https://webgenius-6nph.onrender.com';

export const config = {
  apiBaseUrl: API_BASE_URL,
  isDevelopment,
};