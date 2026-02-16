# AI Email Auto-Reply System

Automated customer care email system powered by Google Gemini AI and RAG-based knowledge retrieval. Classifies incoming emails into 4 categories and handles them accordingly — from instant AI replies to flagging critical emails for manual review.


## Prerequisites

- **Python 3.10+** and **Node.js 18+**
- **Docker & Docker Compose** (optional)
- **Gmail API** enabled in [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
- **Gemini API Key** from [Google AI Studio](https://aistudio.google.com/app/apikey)

## Setup

### Step 1: Clone and Configure

```bash
git clone <repo-url>
cd Mail_Marketing
cp .env.example .env
# Edit .env and set GEMINI_API_KEY
```

### Step 2: Gmail API Credentials

1. In Google Cloud Console, enable **Gmail API**
2. Create **OAuth 2.0 Client ID** (Desktop App)
3. Download the JSON and place it:

```bash
mkdir credentials
mv ~/Downloads/client_secret_*.json credentials/credentials.json
```

### Step 3: Authenticate Gmail (One-Time)

Run locally (not in Docker) — opens a browser for OAuth:

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
GMAIL_CREDENTIALS_PATH=../credentials/credentials.json GMAIL_TOKEN_PATH=../credentials/token.json python -c "from services.gmail_service import get_gmail_service; get_gmail_service()"
cd ..
```

After authorizing in the browser, `token.json` is saved in `credentials/`. This only needs to be done once.

### Step 4: Run

**Docker (Recommended):**

```bash
docker compose up --build -d
docker compose logs -f          # View logs
docker compose down             # Stop
```

**Manual (Without Docker):**

```bash
# Terminal 1 — Backend
cd backend
source .venv/bin/activate
uvicorn main:app --reload --port 8020

# Terminal 2 — Frontend
cd frontend
npm install && npm run dev
```

### Step 5: Access

- **Frontend:** http://localhost:5173
- **API Docs:** http://localhost:8020/docs

## Project Structure

```
Mail_Marketing/
├── backend/
│   ├── main.py                  # FastAPI app, scheduler, routes
│   ├── config.py                # Environment config
│   ├── database.py              # SQLite with FTS5 search
│   ├── models/schemas.py        # Pydantic models
│   ├── services/
│   │   ├── gmail_service.py     # Gmail API integration
│   │   ├── ai_service.py        # Gemini AI calls
│   │   ├── rag_service.py       # ChromaDB RAG pipeline
│   │   ├── classifier.py        # Email classification
│   │   ├── email_processor.py   # Main processing loop
│   │   ├── blocklist_service.py # Sender filtering
│   │   └── retry_service.py     # Retry queue with backoff
│   └── routes/
│       ├── emails.py            # Email CRUD + compose
│       ├── drafts.py            # Draft review workflow
│       ├── knowledge.py         # Knowledge base upload
│       ├── blocklist.py         # Blocklist management
│       ├── analytics.py         # Analytics data
│       ├── search.py            # Full-text search
│       ├── bulk.py              # Bulk actions
│       └── retry.py             # Retry queue management
├── frontend/src/
│   ├── App.jsx                  # Main layout with tab navigation
│   ├── services/api.js          # Axios API client
│   └── components/
│       ├── Dashboard.jsx        # System overview
│       ├── Analytics.jsx        # Charts (recharts)
│       ├── EmailList.jsx        # Pending emails + bulk actions
│       ├── EmailComposer.jsx    # Compose new emails
│       ├── DraftReview.jsx      # Review AI drafts
│       ├── KnowledgeBase.jsx    # Upload knowledge files
│       ├── EmailHistory.jsx     # Sent email history
│       └── Settings.jsx         # Settings, blocklist, retry queue
├── credentials/                 # OAuth credentials (gitignored)
├── docker-compose.yml
└── .env
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GEMINI_API_KEY` | Google Gemini API key | (required) |
| `POLLING_INTERVAL_MINUTES` | Email check interval (minutes) | `3` |

