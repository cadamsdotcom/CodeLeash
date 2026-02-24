# Multi-stage build for CodeLeash Web Server

# Build arguments
ARG GIT_COMMIT_SHA=unset

# Frontend builder stage
FROM node:22-alpine AS frontend-builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install Node.js dependencies
RUN npm ci

# Copy only frontend source files (not Python code)
COPY src ./src
COPY vite.config.js tsconfig.json tailwind.config.js postcss.config.js ./

# Build frontend assets
RUN npm run build

# Python builder stage for compiling dependencies
FROM python:3.12-slim AS python-builder

WORKDIR /app

# Install build dependencies for Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    python3-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install --no-cache-dir uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Create empty README.md for Python package build
RUN touch README.md

# Install Python dependencies
RUN uv sync --frozen --no-dev

# Production stage
FROM python:3.12-slim

# Pass through build argument
ARG GIT_COMMIT_SHA=unset

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install --no-cache-dir uv

# Layer ordering optimized for cache efficiency (least → most frequently changing)

# 1. Copy dependency files (rarely change)
COPY pyproject.toml uv.lock ./
RUN touch README.md

# 2. Copy venv from builder (changes when deps change)
COPY --from=python-builder /app/.venv ./.venv

# 3. Copy static files (change occasionally)
COPY static ./static

# 4. Copy frontend assets (change with frontend code)
COPY --from=frontend-builder /app/dist ./dist

# 5. Copy entrypoints (change occasionally)
COPY main.py worker.py ./

# 6. Copy app code last (changes most frequently)
COPY app ./app

# Create non-root user
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app

USER app

# Expose port
EXPOSE 8000

# Set environment variables
ENV ENVIRONMENT=production
ENV PYTHONPATH=/app
ENV GIT_COMMIT_SHA=${GIT_COMMIT_SHA}

# Health check using Python instead of curl
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD uv run python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/').read()" || exit 1

# Start the web application
CMD ["uv", "run", "python", "main.py"]