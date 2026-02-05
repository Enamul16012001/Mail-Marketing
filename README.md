# AI Email Auto-Reply System

Automated email response system for customer care using Google Gemini AI and RAG-based knowledge retrieval.

## Features

- **Auto-classify emails** into 4 categories:
  - Generic → Instant AI reply
  - Knowledge-based → RAG-powered reply
  - Critical → Flagged for manual reply
  - Complex → Draft for review

- **RAG Knowledge Base** - Upload PDF/DOCX/TXT files
- **Draft Review** - Edit AI responses before sending
- **Dashboard** - Monitor and manage emails

## Quick Start

### 1. Setup Environment

```bash
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

### 2. Authenticate Gmail (first time only)

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python -c "from services.gmail_service import get_gmail_service; get_gmail_service()"
```

This opens a browser for OAuth. The generated `token.json` will be used by Docker.

### 3. Run with Docker

```bash
# Build and start containers
docker compose up --build -d

# View logs
docker compose logs -f

# Stop containers
docker compose down

# Rebuild after code changes
docker compose up --build -d
```

### 4. Access

- **Frontend**: http://localhost:5173
- **API Docs**: http://localhost:8020/docs

## Docker Commands Reference

```bash
# Start in background
docker compose up -d

# Start with live logs
docker compose up

# Rebuild images
docker compose build

# Stop all containers
docker compose down

# Stop and remove volumes (reset data)
docker compose down -v

# View backend logs only
docker compose logs -f backend

# Restart a specific service
docker compose restart backend
```

## Manual Setup (without Docker)

```bash
# Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8020

# Frontend (new terminal)
cd frontend
npm install && npm run dev
```

## Tech Stack

- **Backend**: FastAPI, ChromaDB, Google Gemini
- **Frontend**: React, Tailwind CSS
- **Email**: Gmail API

## Environment Variables

| Variable | Description |
|----------|-------------|
| `GEMINI_API_KEY` | Google Gemini API key |
| `POLLING_INTERVAL_MINUTES` | Email check interval (default: 3) |
