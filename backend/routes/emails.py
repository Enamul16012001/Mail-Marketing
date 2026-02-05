from fastapi import APIRouter, HTTPException
from typing import List
from datetime import datetime

from models.schemas import Email, EmailReply, EmailStatus
from services.gmail_service import get_gmail_service
from database import get_database

router = APIRouter(prefix="/api/emails", tags=["emails"])


@router.get("/pending", response_model=List[Email])
async def get_pending_emails():
    """Get emails that need manual reply."""
    db = get_database()
    return db.get_pending_emails()


@router.get("/history", response_model=List[Email])
async def get_email_history(limit: int = 50):
    """Get sent email history."""
    db = get_database()
    return db.get_email_history(limit)


@router.get("/{email_id}", response_model=Email)
async def get_email(email_id: str):
    """Get a specific email."""
    db = get_database()
    email = db.get_email(email_id)
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    return email


@router.post("/reply")
async def send_manual_reply(reply: EmailReply):
    """Send a manual reply to an email."""
    gmail = get_gmail_service()
    db = get_database()

    # Send the email
    message_id = gmail.send_email(reply)

    if not message_id:
        raise HTTPException(status_code=500, detail="Failed to send email")

    # Update original email status if we have the reference
    if reply.thread_id:
        # Find the original email by thread_id and update
        # This is a simplified approach
        pass

    return {
        "success": True,
        "message_id": message_id
    }


@router.post("/reply/{email_id}")
async def reply_to_email(email_id: str, body: dict):
    """Reply to a specific email."""
    gmail = get_gmail_service()
    db = get_database()

    # Get original email
    email = db.get_email(email_id)
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")

    response_body = body.get("response", "")
    if not response_body:
        raise HTTPException(status_code=400, detail="Response body required")

    # Send reply
    message_id = gmail.reply_to_email(email, response_body)

    if not message_id:
        raise HTTPException(status_code=500, detail="Failed to send reply")

    # Update email status
    db.update_email_status(email_id, EmailStatus.REPLIED, response_body)

    return {
        "success": True,
        "message_id": message_id
    }


@router.post("/process")
async def trigger_email_processing():
    """Manually trigger email processing."""
    from services.email_processor import process_new_emails

    try:
        processed = process_new_emails()
        return {
            "success": True,
            "processed_count": processed
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{email_id}")
async def dismiss_email(email_id: str):
    """Dismiss/archive a pending email."""
    db = get_database()

    email = db.get_email(email_id)
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")

    # Mark email as read in Gmail
    gmail = get_gmail_service()
    gmail.mark_as_read(email_id)

    # Update status to indicate it was dismissed
    db.update_email_status(email_id, EmailStatus.REPLIED, "[Dismissed by user]")

    return {"success": True}
