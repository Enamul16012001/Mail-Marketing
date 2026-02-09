from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler

from config import POLLING_INTERVAL_MINUTES
from routes import emails, drafts, knowledge, blocklist, retry, search, bulk, analytics
from services.email_processor import get_polling_service, process_new_emails, initialize_system
from services.rag_service import get_rag_service
from database import get_database


# Background scheduler
scheduler = BackgroundScheduler()


def scheduled_email_check():
    """Scheduled task to check for new emails."""
    service = get_polling_service()
    if service.is_running:
        try:
            count = process_new_emails()
            if count > 0:
                print(f"Processed {count} new emails")
        except Exception as e:
            print(f"Email check failed: {e}")


def scheduled_retry_check():
    """Scheduled task to process retry queue."""
    try:
        from services.retry_service import get_retry_service
        retry_service = get_retry_service()
        count = retry_service.process_retries()
        if count > 0:
            print(f"Processed {count} retries")
    except Exception as e:
        print(f"Retry check failed: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    print("Starting AI Email Auto-Reply System...")

    # Initialize services
    get_database()
    get_rag_service()

    # Start polling service
    polling_service = get_polling_service()
    polling_service.start()

    # First-run initialization (marks existing emails as seen, won't reply to old emails)
    try:
        initialize_system()
        print("Gmail initialized successfully")
    except Exception as e:
        print(f"Gmail initialization skipped (will retry on first request): {e}")

    # Schedule email polling
    scheduler.add_job(
        scheduled_email_check,
        'interval',
        minutes=POLLING_INTERVAL_MINUTES,
        id='email_polling'
    )

    # Schedule retry processing (every minute)
    scheduler.add_job(
        scheduled_retry_check,
        'interval',
        minutes=1,
        id='retry_processing'
    )

    scheduler.start()
    print(f"Email polling started (every {POLLING_INTERVAL_MINUTES} minutes)")
    print("Retry processing started (every 1 minute)")

    yield

    # Shutdown
    print("Shutting down...")
    polling_service.stop()
    scheduler.shutdown()


# Create FastAPI app
app = FastAPI(
    title="AI Email Auto-Reply System",
    description="Automated email response system using AI classification and RAG",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(emails.router)
app.include_router(drafts.router)
app.include_router(knowledge.router)
app.include_router(blocklist.router)
app.include_router(retry.router)
app.include_router(search.router)
app.include_router(bulk.router)
app.include_router(analytics.router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "AI Email Auto-Reply System",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/api/stats")
async def get_stats():
    """Get system statistics."""
    db = get_database()
    rag = get_rag_service()

    email_stats = db.get_stats()
    rag_stats = rag.get_stats()

    return {
        **email_stats,
        "knowledge_files": rag_stats["total_files"],
        "knowledge_chunks": rag_stats["total_chunks"]
    }


@app.get("/api/settings")
async def get_settings():
    """Get current settings."""
    db = get_database()

    return {
        "polling_interval": int(db.get_setting("polling_interval") or POLLING_INTERVAL_MINUTES),
        "auto_reply_enabled": db.get_setting("auto_reply_enabled") == "true"
    }


@app.post("/api/settings")
async def update_settings(settings: dict):
    """Update settings."""
    db = get_database()

    if "polling_interval" in settings:
        db.set_setting("polling_interval", str(settings["polling_interval"]))

    if "auto_reply_enabled" in settings:
        db.set_setting("auto_reply_enabled", "true" if settings["auto_reply_enabled"] else "false")

    return {"success": True}


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    db = get_database()
    return {
        "status": "healthy",
        "polling_active": get_polling_service().is_running,
        "initialized": db.get_setting("system_initialized") == "true",
        "initialized_at": db.get_setting("initialized_at")
    }


@app.post("/api/initialize")
async def manual_initialize():
    """Manually run initialization (marks existing emails as seen)."""
    db = get_database()

    # Reset initialization flag to force re-initialization
    db.set_setting("system_initialized", "false")

    # Run initialization
    count = initialize_system()

    return {
        "success": True,
        "emails_marked_as_seen": count,
        "message": f"Marked {count} existing emails as seen. New emails will be processed normally."
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
