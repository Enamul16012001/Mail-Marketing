from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
import uuid

from models.schemas import DraftEdit, EmailStatus
from services.gmail_service import get_gmail_service
from database import get_database

router = APIRouter(prefix="/api/drafts", tags=["drafts"])


@router.get("", response_model=List[Dict[str, Any]])
async def get_pending_drafts():
    """Get drafts awaiting approval."""
    db = get_database()
    return db.get_pending_drafts()


@router.get("/{draft_id}")
async def get_draft(draft_id: str):
    """Get a specific draft."""
    db = get_database()
    draft = db.get_draft(draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    return draft


@router.post("/{draft_id}/approve")
async def approve_draft(draft_id: str):
    """Approve and send a draft."""
    db = get_database()
    gmail = get_gmail_service()

    # Get draft
    draft = db.get_draft(draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")

    if draft["status"] != "pending":
        raise HTTPException(status_code=400, detail="Draft is not pending")

    # Send the draft via Gmail
    gmail_draft_id = draft["gmail_draft_id"]
    message_id = gmail.send_draft(gmail_draft_id)

    if not message_id:
        raise HTTPException(status_code=500, detail="Failed to send draft")

    # Update draft status
    db.update_draft_status(draft_id, "approved")

    # Update original email status
    db.update_email_status(draft["email_id"], EmailStatus.REPLIED)

    return {
        "success": True,
        "message_id": message_id
    }


@router.put("/{draft_id}")
async def edit_draft(draft_id: str, edit: DraftEdit):
    """Edit a draft's content."""
    db = get_database()
    gmail = get_gmail_service()

    # Get existing draft
    draft = db.get_draft(draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")

    # Get original email
    original_email = db.get_email(draft["email_id"])
    if not original_email:
        raise HTTPException(status_code=404, detail="Original email not found")

    # Delete old Gmail draft
    gmail.delete_draft(draft["gmail_draft_id"])

    # Create new draft with edited content
    from models.schemas import EmailReply

    subject = original_email.subject
    if not subject.lower().startswith("re:"):
        subject = f"Re: {subject}"

    reply = EmailReply(
        to=original_email.sender,
        subject=subject,
        body=edit.content,
        thread_id=original_email.thread_id
    )

    new_gmail_draft_id = gmail.create_draft(reply)

    if not new_gmail_draft_id:
        raise HTTPException(status_code=500, detail="Failed to create updated draft")

    # Update draft in database
    with db._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE drafts
            SET gmail_draft_id = ?, ai_response = ?
            WHERE id = ?
        """, (new_gmail_draft_id, edit.content, draft_id))
        conn.commit()

    return {
        "success": True,
        "draft_id": draft_id
    }


@router.delete("/{draft_id}")
async def discard_draft(draft_id: str):
    """Discard a draft."""
    db = get_database()
    gmail = get_gmail_service()

    # Get draft
    draft = db.get_draft(draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")

    # Delete Gmail draft
    gmail.delete_draft(draft["gmail_draft_id"])

    # Update draft status
    db.update_draft_status(draft_id, "discarded")

    # Update email status to pending manual (so it shows up again)
    db.update_email_status(draft["email_id"], EmailStatus.MANUAL_REQUIRED)

    return {"success": True}
