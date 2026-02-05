import uuid
from datetime import datetime
from typing import Optional

from models.schemas import Email, EmailCategory, EmailStatus, EmailReply
from services.gmail_service import get_gmail_service
from services.classifier import get_classifier
from database import get_database


def initialize_system() -> int:
    """
    First-run initialization: mark all existing unread emails as 'seen'
    without processing them. This prevents auto-replying to old emails.
    Returns the number of emails marked as seen.
    """
    db = get_database()

    # Check if already initialized
    if db.get_setting("system_initialized") == "true":
        return 0

    print("First run detected - marking existing emails as seen...")
    gmail = get_gmail_service()

    # Get all unread emails (up to 100)
    emails = gmail.get_unread_emails(max_results=100)
    count = 0

    for email in emails:
        # Mark as seen in our database (but don't process or reply)
        email.category = None
        email.status = EmailStatus.REPLIED  # Mark as handled
        email.ai_response = "[Skipped - existed before system start]"
        email.processed_at = datetime.now()
        db.save_email(email)
        count += 1

    # Mark system as initialized
    db.set_setting("system_initialized", "true")
    db.set_setting("initialized_at", datetime.now().isoformat())

    print(f"Initialization complete - marked {count} existing emails as seen")
    return count


def process_new_emails() -> int:
    """
    Process new unread emails.
    Returns the number of emails processed.
    """
    gmail = get_gmail_service()
    classifier = get_classifier()
    db = get_database()

    # Get unread emails
    emails = gmail.get_unread_emails(max_results=20)
    processed_count = 0

    for email in emails:
        # Skip if already processed
        if db.is_email_processed(email.id):
            continue

        try:
            processed_count += 1
            process_single_email(email, gmail, classifier, db)
        except Exception as e:
            print(f"Error processing email {email.id}: {e}")
            # Save email as pending manual on error
            email.category = EmailCategory.PENDING_MANUAL
            email.status = EmailStatus.MANUAL_REQUIRED
            email.processed_at = datetime.now()
            db.save_email(email)

    return processed_count


def process_single_email(
    email: Email,
    gmail,
    classifier,
    db
) -> None:
    """Process a single email."""

    # Classify and generate response
    classification, response = classifier.process_email(email)

    # Update email with classification
    email.category = classification.category
    email.ai_response = response
    email.processed_at = datetime.now()

    # Handle based on category
    if classification.category == EmailCategory.AUTO_REPLY:
        # Send immediate reply
        if response:
            message_id = gmail.reply_to_email(email, response)
            if message_id:
                email.status = EmailStatus.REPLIED
                # Mark original as read
                gmail.mark_as_read(email.id)
            else:
                # Failed to send, mark as manual
                email.status = EmailStatus.MANUAL_REQUIRED
        else:
            email.status = EmailStatus.MANUAL_REQUIRED

    elif classification.category == EmailCategory.RAG_REPLY:
        # Send RAG-based reply
        if response:
            message_id = gmail.reply_to_email(email, response)
            if message_id:
                email.status = EmailStatus.REPLIED
                gmail.mark_as_read(email.id)
            else:
                email.status = EmailStatus.MANUAL_REQUIRED
        else:
            email.status = EmailStatus.MANUAL_REQUIRED

    elif classification.category == EmailCategory.DRAFT_REVIEW:
        # Create draft for review
        if response:
            # Prepare reply
            subject = email.subject
            if not subject.lower().startswith("re:"):
                subject = f"Re: {subject}"

            reply = EmailReply(
                to=email.sender,
                subject=subject,
                body=response,
                thread_id=email.thread_id
            )

            gmail_draft_id = gmail.create_draft(reply)

            if gmail_draft_id:
                email.status = EmailStatus.DRAFT

                # Save draft info
                draft_id = str(uuid.uuid4())
                db.save_draft(draft_id, email.id, gmail_draft_id, response)

                # Mark as read since we've processed it
                gmail.mark_as_read(email.id)
            else:
                email.status = EmailStatus.MANUAL_REQUIRED
        else:
            email.status = EmailStatus.MANUAL_REQUIRED

    elif classification.category == EmailCategory.PENDING_MANUAL:
        # Needs human attention
        email.status = EmailStatus.MANUAL_REQUIRED
        # Don't mark as read - keep visible in inbox

    # Save email to database
    db.save_email(email)


class EmailPollingService:
    """Background service for polling emails."""

    def __init__(self):
        self.is_running = False

    def start(self):
        """Mark service as running."""
        self.is_running = True

    def stop(self):
        """Mark service as stopped."""
        self.is_running = False

    def poll(self):
        """Execute a single poll cycle."""
        if not self.is_running:
            return 0

        try:
            return process_new_emails()
        except Exception as e:
            print(f"Polling error: {e}")
            return 0


# Singleton instance
_polling_service: Optional[EmailPollingService] = None


def get_polling_service() -> EmailPollingService:
    """Get or create polling service."""
    global _polling_service
    if _polling_service is None:
        _polling_service = EmailPollingService()
    return _polling_service
