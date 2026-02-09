from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List

from models.schemas import EmailStatus
from services.gmail_service import get_gmail_service
from database import get_database

router = APIRouter(prefix="/api/emails/bulk", tags=["bulk"])


class BulkDismiss(BaseModel):
    email_ids: List[str]


class BulkReply(BaseModel):
    email_ids: List[str]
    response: str


@router.post("/dismiss")
async def bulk_dismiss(body: BulkDismiss):
    """Dismiss multiple pending emails at once."""
    if not body.email_ids:
        raise HTTPException(status_code=400, detail="No email IDs provided")

    db = get_database()
    gmail = get_gmail_service()
    dismissed = 0

    for email_id in body.email_ids:
        email = db.get_email(email_id)
        if email and email.status == EmailStatus.MANUAL_REQUIRED:
            gmail.mark_as_read(email_id)
            db.update_email_status(email_id, EmailStatus.REPLIED, "[Dismissed by user]")
            dismissed += 1

    return {"success": True, "dismissed": dismissed}


@router.post("/reply")
async def bulk_reply(body: BulkReply):
    """Send the same reply to multiple pending emails."""
    if not body.email_ids:
        raise HTTPException(status_code=400, detail="No email IDs provided")
    if not body.response.strip():
        raise HTTPException(status_code=400, detail="Response body is required")

    db = get_database()
    gmail = get_gmail_service()
    sent = 0
    failed = 0

    for email_id in body.email_ids:
        email = db.get_email(email_id)
        if not email:
            failed += 1
            continue

        message_id = gmail.reply_to_email(email, body.response)
        if message_id:
            db.update_email_status(email_id, EmailStatus.REPLIED, body.response)
            gmail.mark_as_read(email_id)
            sent += 1
        else:
            failed += 1

    return {"success": True, "sent": sent, "failed": failed}
