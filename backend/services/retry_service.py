import uuid
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict

from database import get_database
from services.gmail_service import get_gmail_service
from models.schemas import EmailReply, EmailStatus

BACKOFF_MINUTES = [1, 5, 15, 30, 60]


class RetryService:
    """Manages retry queue for failed email operations."""

    def __init__(self):
        self.db = get_database()

    def add_to_queue(self, email_id: str, action: str,
                     payload: dict, error: str, max_attempts: int = 5):
        """Add a failed operation to the retry queue."""
        retry_id = str(uuid.uuid4())
        self.db.add_retry(
            retry_id, email_id, action,
            json.dumps(payload), error, max_attempts
        )

    def process_retries(self) -> int:
        """Process all due retries. Called by scheduler."""
        items = self.db.get_due_retries()
        if not items:
            return 0

        gmail = get_gmail_service()
        count = 0
        for item in items:
            count += 1
            self._retry_single(item, gmail)
        return count

    def _retry_single(self, item: Dict, gmail):
        """Attempt a single retry."""
        payload = json.loads(item["payload"])
        attempt = item["attempt_count"] + 1

        try:
            if item["action"] == "send_reply":
                reply = EmailReply(**payload)
                message_id = gmail.send_email(reply)
                if not message_id:
                    raise Exception("send_email returned None")
                # Success
                self.db.update_retry_status(item["id"], "succeeded")
                self.db.update_email_status(
                    item["email_id"], EmailStatus.REPLIED, payload.get("body")
                )
                return

            elif item["action"] == "send_draft":
                draft_id = payload.get("gmail_draft_id")
                if draft_id:
                    message_id = gmail.send_draft(draft_id)
                    if not message_id:
                        raise Exception("send_draft returned None")
                    self.db.update_retry_status(item["id"], "succeeded")
                    return

            raise Exception(f"Unknown action: {item['action']}")

        except Exception as e:
            if attempt >= item["max_attempts"]:
                self.db.update_retry_status(item["id"], "failed")
            else:
                backoff_idx = min(attempt, len(BACKOFF_MINUTES) - 1)
                next_retry = datetime.now() + timedelta(minutes=BACKOFF_MINUTES[backoff_idx])
                self.db.update_retry(
                    item["id"], attempt, str(e), next_retry.isoformat()
                )

    def get_queue(self) -> List[Dict]:
        """Get all retry queue items for display."""
        return self.db.get_retry_queue()

    def manual_retry(self, retry_id: str) -> bool:
        """Reset a retry item to be processed immediately."""
        now = datetime.now().isoformat()
        return self.db.update_retry(retry_id, 0, "Manual retry triggered", now)

    def cancel_retry(self, retry_id: str) -> bool:
        """Remove item from retry queue."""
        return self.db.delete_retry(retry_id)


# Singleton
_retry_service: Optional[RetryService] = None


def get_retry_service() -> RetryService:
    global _retry_service
    if _retry_service is None:
        _retry_service = RetryService()
    return _retry_service
