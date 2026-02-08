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

### 1. Clone and Setup Environment

```bash
git clone <repo-url>
cd Mail_Marketing
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

### 2. Setup Gmail Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Create a project → Enable **Gmail API**
3. Create **OAuth 2.0 Client ID** (Desktop App)
4. Download the JSON and place it in the project:

```bash
mkdir -p credentials
# Move your downloaded OAuth JSON file:
mv ~/Downloads/client_secret_*.json credentials/credentials.json
```

### 3. Authenticate Gmail (first time only)

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
GMAIL_CREDENTIALS_PATH=../credentials/credentials.json GMAIL_TOKEN_PATH=../credentials/token.json python -c "from services.gmail_service import get_gmail_service; get_gmail_service()"
```

This opens a browser for OAuth. The generated `token.json` is saved in the `credentials/` folder.

### 4. Run with Docker

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

### 5. Access

- **Frontend**: http://localhost:5173
- **API Docs**: http://localhost:8020/docs

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
