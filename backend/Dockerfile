# ─────────────────────────────────────────
# BASE IMAGE
# Python 3.12 slim variant
# Slim = smaller size, fewer system tools
# Faster builds, smaller attack surface
# ─────────────────────────────────────────
FROM python:3.12-slim


# ─────────────────────────────────────────
# ENVIRONMENT VARIABLES
# Set before any other commands
# PYTHONDONTWRITEBYTECODE — no .pyc files
# PYTHONUNBUFFERED — print statements appear
# immediately in Docker logs
# ─────────────────────────────────────────
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1


# ─────────────────────────────────────────
# WORKING DIRECTORY
# All subsequent commands run from here
# Files are copied into here
# ─────────────────────────────────────────
WORKDIR /app


# ─────────────────────────────────────────
# SYSTEM DEPENDENCIES
# gcc — needed by some Python packages
#       that compile C extensions
# Clean apt cache after install to
# keep image size small
# ─────────────────────────────────────────
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*


# ─────────────────────────────────────────
# PYTHON DEPENDENCIES
# Copy requirements FIRST before code
# This is the critical caching optimization:
#
# If code changes  → only code layer rebuilds
# If requirements  → everything below rebuilds
# change
#
# By copying requirements first, pip install
# layer is cached as long as requirements.txt
# does not change — even if code changes
# ─────────────────────────────────────────
COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt


# ─────────────────────────────────────────
# APPLICATION CODE
# Copied AFTER dependencies for caching
# Only contains the app/ directory
# .env and other sensitive files are
# excluded via .dockerignore
# ─────────────────────────────────────────
COPY ./app ./app


# ─────────────────────────────────────────
# PORT
# Document that container listens on 8000
# Does not actually publish the port
# Publishing is done in docker-compose.yml
# ─────────────────────────────────────────
EXPOSE 8000


# ─────────────────────────────────────────
# STARTUP COMMAND
# uvicorn — production grade ASGI server
# app.main:app — file app/main.py,
#                FastAPI instance named app
# --host 0.0.0.0 — accept connections from
#                  outside the container
# --port 8000    — listen on port 8000
# --reload       — auto reload on code changes
#                  DEVELOPMENT ONLY
#                  remove for production
# ─────────────────────────────────────────
CMD ["uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--reload"]
