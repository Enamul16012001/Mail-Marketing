# AI Email Auto-Reply System

Automated customer care email system powered by Google Gemini AI and RAG-based knowledge retrieval. Classifies incoming emails into 4 categories and handles them accordingly — from instant AI replies to flagging critical emails for manual review.


## Prerequisites

- **Python 3.10+**
- **Node.js 18+**
- **Docker & Docker Compose** (if running with Docker)
- **Google Cloud Project** with Gmail API enabled
- **Gemini API Key** from [Google AI Studio](https://aistudio.google.com/app/apikey)

## Setup

### Step 1: Clone and Configure

```bash
git clone <repo-url>
cd Mail_Marketing
cp .env.example .env
```

Edit `.env` and add your Gemini API key:

```
GEMINI_API_KEY=your_actual_key_here
```

### Step 2: Setup Gmail API Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Create a project (or select existing) and enable the **Gmail API**
3. Go to **Credentials** > **Create Credentials** > **OAuth 2.0 Client ID**
4. Application type: **Desktop App**
5. Download the JSON file

Place it in the project:

```bash
mkdir credentials
```

- **Linux/macOS:** `mv ~/Downloads/client_secret_*.json credentials/credentials.json`
- **Windows:** `move %USERPROFILE%\Downloads\client_secret_*.json credentials\credentials.json`

### Step 3: Authenticate Gmail (One-Time)

This must be done locally (not inside Docker) because it opens a browser for OAuth consent.

**Linux/macOS:**

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
GMAIL_CREDENTIALS_PATH=../credentials/credentials.json GMAIL_TOKEN_PATH=../credentials/token.json python -c "from services.gmail_service import get_gmail_service; get_gmail_service()"
```

**Windows (PowerShell):**

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:GMAIL_CREDENTIALS_PATH="../credentials/credentials.json"
$env:GMAIL_TOKEN_PATH="../credentials/token.json"
python -c "from services.gmail_service import get_gmail_service; get_gmail_service()"
```

**Windows (CMD):**

```cmd
cd backend
python -m venv .venv
.venv\Scripts\activate.bat
pip install -r requirements.txt
set GMAIL_CREDENTIALS_PATH=../credentials/credentials.json
set GMAIL_TOKEN_PATH=../credentials/token.json
python -c "from services.gmail_service import get_gmail_service; get_gmail_service()"
```

A browser window will open for Google OAuth. After authorizing, a `token.json` file is saved in `credentials/`. This only needs to be done once.

### Step 4: Run the Application

#### Option A: Docker (Recommended)

```bash
docker compose up --build -d
```

Useful commands:

```bash
docker compose logs -f        # View logs
docker compose down            # Stop
docker compose up --build -d   # Rebuild after code changes
```

#### Option B: Manual (Without Docker)

**Terminal 1 — Backend:**

```bash
cd backend
source .venv/bin/activate          # Linux/macOS
# .venv\Scripts\Activate.ps1      # Windows PowerShell
pip install -r requirements.txt
uvicorn main:app --reload --port 8020
```

**Terminal 2 — Frontend:**

```bash
cd frontend
npm install
npm run dev
```

### Step 5: Access

| Service | URL |
|---------|-----|
| Frontend | http://localhost:5173 |
| API Docs | http://localhost:8020/docs |

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
| `POLLING_INTERVAL_MINUTES` | Email check interval in minutes | `3` |

## Tech Stack

- **Backend:** FastAPI, SQLite (FTS5), ChromaDB, Google Gemini, APScheduler
- **Frontend:** React 18, Tailwind CSS, Recharts, Heroicons
- **Email:** Gmail API (OAuth 2.0)
- **Deployment:** Docker Compose
