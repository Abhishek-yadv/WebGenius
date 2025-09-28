# Stage 1: Build Frontend
FROM node:18-alpine as frontend-builder

WORKDIR /app/frontend

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build the frontend
RUN npm run build

# Stage 2: Python Backend with Frontend
# Stage 2: Python Backend with Frontend
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for Python + Playwright Chromium
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    curl \
    fonts-dejavu \
    fonts-liberation \
    fonts-noto-core \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libxshmfence1 \
    libnss3 \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python requirements
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright + Chromium
RUN pip install playwright
RUN playwright install chromium

# Copy backend code
COPY backend/ ./backend/

# Copy frontend build
COPY --from=frontend-builder /app/frontend/dist ./static

# Create directories
RUN mkdir -p /app/scraped_data /app/output /app/debug

# Environment
ENV PYTHONPATH=/app
ENV PORT=5000
ENV NODE_ENV=production

# Non-root user
RUN useradd --create-home --shell /bin/bash webgen
RUN chown -R webgen:webgen /app
USER webgen

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/health || exit 1

# Expose port
EXPOSE 5000

# Run app
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "5000"]
