# ───────────────────────────────────────────────────────────────────────────
# Stage 1: Build React frontend
# ───────────────────────────────────────────────────────────────────────────
FROM node:16-alpine AS frontend-builder

WORKDIR /opensky-db/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

# ───────────────────────────────────────────────────────────────────────────
# Stage 2: Build Python backend & bundle frontend
# ───────────────────────────────────────────────────────────────────────────
FROM python:3.9-slim AS backend

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /opensky-db

# System tools
RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential \
 && rm -rf /var/lib/apt/lists/*

# Python deps
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App code
COPY backend/ .  

# Copy React build into backend path
RUN mkdir -p client/build
COPY --from=frontend-builder /opensky-db/frontend/build client/build

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
