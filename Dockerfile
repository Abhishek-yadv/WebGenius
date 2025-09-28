# =========================
# Stage 1: Build Frontend
# =========================
FROM node:18-alpine AS frontend-builder

WORKDIR /app/frontend

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build the frontend
RUN npm run build


# =========================
# Stage 2: Python Backend + Frontend
# =========================
FROM python:3.12-slim

WORKDIR /app

# -------------------------
# Install system dependencies
# -------------------------
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    curl \
    ca-certificates \
    libnss3 \
    libatk-bridge2.0-0 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

# -------------------------
# Install Python dependencies
# -------------------------
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# -------------------------
# Install Playwright globally
# -------------------------
ENV PLAYWRIGHT_BROWSERS_PATH=/usr/local/share/ms-playwright
RUN pip install --no-cache-dir playwright
RUN playwright install chromium

# -------------------------
# Copy backend and frontend
# -------------------------
COPY backend/ ./backend/
COPY --from=frontend-builder /app/frontend/dist ./static

# -------------------------
# Create directories
# -------------------------
RUN mkdir -p /app/scraped_data /app/output /app/debug

# -------------------------
# Create non-root user
# -------------------------
RUN useradd --create-home --shell /bin/bash webgen
RUN chown -R webgen:webgen /app /usr/local/share/ms-playwright
USER webgen

# -------------------------
# Environment variables
# -------------------------
ENV PYTHONPATH=/app
ENV PORT=5000
ENV NODE_ENV=production

# -------------------------
# Health check & port
# -------------------------
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/health || exit 1

EXPOSE 5000

# -------------------------
# Run the backend
# -------------------------
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "5000"]
