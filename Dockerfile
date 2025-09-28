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
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python requirements
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright and browsers
RUN playwright install chromium
RUN playwright install-deps chromium

# Copy backend code
COPY backend/ ./backend/

# Copy built frontend from previous stage
COPY --from=frontend-builder /app/frontend/dist ./static

# Create necessary directories
RUN mkdir -p /app/scraped_data /app/output /app/debug

# Set environment variables
ENV PYTHONPATH=/app
ENV PORT=5000
ENV NODE_ENV=production

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash webgen
RUN chown -R webgen:webgen /app
USER webgen

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/health || exit 1

# Expose port
EXPOSE 5000

# Run the application
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "5000"]
