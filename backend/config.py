import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = Path(__file__).resolve().parent

# Gmail configuration
GMAIL_CREDENTIALS_PATH = os.getenv("GMAIL_CREDENTIALS_PATH", str(BASE_DIR / "credentials.json"))
GMAIL_TOKEN_PATH = os.getenv("GMAIL_TOKEN_PATH", str(BASE_DIR / "token.json"))
GMAIL_SCOPES = ["https://mail.google.com/"]

# Gemini AI configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# ChromaDB configuration
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", str(BACKEND_DIR / "chroma_db"))
Path(CHROMA_PERSIST_DIR).mkdir(parents=True, exist_ok=True)

# Knowledge base path
KNOWLEDGE_BASE_DIR = BACKEND_DIR / "knowledge_base"
KNOWLEDGE_BASE_DIR.mkdir(exist_ok=True)

# Email polling configuration
POLLING_INTERVAL_MINUTES = int(os.getenv("POLLING_INTERVAL_MINUTES", "3"))

# Database path
DATABASE_PATH = BACKEND_DIR / "data" / "email_data.db"
DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

# Classification labels
class EmailCategory:
    AUTO_REPLY = "auto_reply"           # Generic emails - instant AI reply
    RAG_REPLY = "rag_reply"             # Knowledge-based - RAG query + reply
    PENDING_MANUAL = "pending_manual"   # Critical - needs human
    DRAFT_REVIEW = "draft_review"       # AI draft - needs approval
