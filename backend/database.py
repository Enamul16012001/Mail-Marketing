import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from contextlib import contextmanager

from config import DATABASE_PATH
from models.schemas import Email, EmailCategory, EmailStatus


class Database:
    """SQLite database for storing email metadata and processing history."""

    def __init__(self):
        self.db_path = DATABASE_PATH
        self._init_db()

    def _init_db(self):
        """Initialize database tables."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Processed emails table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS emails (
                    id TEXT PRIMARY KEY,
                    thread_id TEXT,
                    sender TEXT,
                    sender_name TEXT,
                    recipient TEXT,
                    subject TEXT,
                    body TEXT,
                    attachments TEXT,
                    received_at TEXT,
                    category TEXT,
                    status TEXT,
                    ai_response TEXT,
                    processed_at TEXT,
                    draft_id TEXT
                )
            """)

            # Drafts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS drafts (
                    id TEXT PRIMARY KEY,
                    email_id TEXT,
                    gmail_draft_id TEXT,
                    ai_response TEXT,
                    created_at TEXT,
                    status TEXT DEFAULT 'pending',
                    FOREIGN KEY (email_id) REFERENCES emails(id)
                )
            """)

            # Settings table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)

            # Initialize default settings
            cursor.execute("""
                INSERT OR IGNORE INTO settings (key, value)
                VALUES ('polling_interval', '3'),
                       ('auto_reply_enabled', 'true')
            """)

            conn.commit()

    @contextmanager
    def _get_connection(self):
        """Get database connection with context manager."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def save_email(self, email: Email) -> bool:
        """Save processed email to database."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            attachments_json = json.dumps([
                {"filename": a.filename, "mime_type": a.mime_type, "size": a.size}
                for a in email.attachments
            ])

            cursor.execute("""
                INSERT OR REPLACE INTO emails
                (id, thread_id, sender, sender_name, recipient, subject, body,
                 attachments, received_at, category, status, ai_response, processed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                email.id,
                email.thread_id,
                email.sender,
                email.sender_name,
                email.recipient,
                email.subject,
                email.body,
                attachments_json,
                email.received_at.isoformat(),
                email.category.value if email.category else None,
                email.status.value,
                email.ai_response,
                email.processed_at.isoformat() if email.processed_at else None
            ))

            conn.commit()
            return True

    def get_email(self, email_id: str) -> Optional[Email]:
        """Get email by ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM emails WHERE id = ?", (email_id,))
            row = cursor.fetchone()

            if row:
                return self._row_to_email(row)
            return None

    def get_pending_emails(self) -> List[Email]:
        """Get emails that need manual reply."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM emails
                WHERE status = 'manual_required'
                ORDER BY received_at DESC
            """)
            rows = cursor.fetchall()
            return [self._row_to_email(row) for row in rows]

    def get_email_history(self, limit: int = 50) -> List[Email]:
        """Get recent email history."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM emails
                WHERE status = 'replied'
                ORDER BY processed_at DESC
                LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()
            return [self._row_to_email(row) for row in rows]

    def update_email_status(
        self,
        email_id: str,
        status: EmailStatus,
        ai_response: Optional[str] = None
    ) -> bool:
        """Update email status and optionally the AI response."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            if ai_response:
                cursor.execute("""
                    UPDATE emails
                    SET status = ?, ai_response = ?, processed_at = ?
                    WHERE id = ?
                """, (status.value, ai_response, datetime.now().isoformat(), email_id))
            else:
                cursor.execute("""
                    UPDATE emails
                    SET status = ?, processed_at = ?
                    WHERE id = ?
                """, (status.value, datetime.now().isoformat(), email_id))

            conn.commit()
            return cursor.rowcount > 0

    def is_email_processed(self, email_id: str) -> bool:
        """Check if an email has already been processed."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM emails WHERE id = ?", (email_id,))
            return cursor.fetchone() is not None

    def _row_to_email(self, row) -> Email:
        """Convert database row to Email object."""
        attachments = json.loads(row["attachments"] or "[]")

        return Email(
            id=row["id"],
            thread_id=row["thread_id"],
            sender=row["sender"],
            sender_name=row["sender_name"],
            recipient=row["recipient"],
            subject=row["subject"],
            body=row["body"],
            attachments=attachments,
            received_at=datetime.fromisoformat(row["received_at"]),
            category=EmailCategory(row["category"]) if row["category"] else None,
            status=EmailStatus(row["status"]) if row["status"] else EmailStatus.PENDING,
            ai_response=row["ai_response"],
            processed_at=datetime.fromisoformat(row["processed_at"]) if row["processed_at"] else None
        )

    # Draft methods
    def save_draft(
        self,
        draft_id: str,
        email_id: str,
        gmail_draft_id: str,
        ai_response: str
    ) -> bool:
        """Save draft information."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO drafts (id, email_id, gmail_draft_id, ai_response, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (draft_id, email_id, gmail_draft_id, ai_response, datetime.now().isoformat()))
            conn.commit()
            return True

    def get_pending_drafts(self) -> List[Dict[str, Any]]:
        """Get drafts awaiting approval."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT d.*, e.sender, e.sender_name, e.subject, e.body, e.received_at
                FROM drafts d
                JOIN emails e ON d.email_id = e.id
                WHERE d.status = 'pending'
                ORDER BY d.created_at DESC
            """)
            rows = cursor.fetchall()

            return [{
                "id": row["id"],
                "email_id": row["email_id"],
                "gmail_draft_id": row["gmail_draft_id"],
                "ai_response": row["ai_response"],
                "created_at": row["created_at"],
                "status": row["status"],
                "original_email": {
                    "sender": row["sender"],
                    "sender_name": row["sender_name"],
                    "subject": row["subject"],
                    "body": row["body"],
                    "received_at": row["received_at"]
                }
            } for row in rows]

    def update_draft_status(self, draft_id: str, status: str) -> bool:
        """Update draft status."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE drafts SET status = ? WHERE id = ?",
                (status, draft_id)
            )
            conn.commit()
            return cursor.rowcount > 0

    def get_draft(self, draft_id: str) -> Optional[Dict[str, Any]]:
        """Get draft by ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM drafts WHERE id = ?", (draft_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None

    def delete_draft(self, draft_id: str) -> bool:
        """Delete a draft."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM drafts WHERE id = ?", (draft_id,))
            conn.commit()
            return cursor.rowcount > 0

    # Settings methods
    def get_setting(self, key: str) -> Optional[str]:
        """Get a setting value."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
            row = cursor.fetchone()
            return row["value"] if row else None

    def set_setting(self, key: str, value: str) -> bool:
        """Set a setting value."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                (key, value)
            )
            conn.commit()
            return True

    # Statistics
    def get_stats(self) -> Dict[str, int]:
        """Get email processing statistics."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            stats = {}

            cursor.execute("SELECT COUNT(*) FROM emails")
            stats["total_emails_processed"] = cursor.fetchone()[0]

            cursor.execute(
                "SELECT COUNT(*) FROM emails WHERE category = ?",
                (EmailCategory.AUTO_REPLY.value,)
            )
            stats["auto_replied"] = cursor.fetchone()[0]

            cursor.execute(
                "SELECT COUNT(*) FROM emails WHERE category = ?",
                (EmailCategory.RAG_REPLY.value,)
            )
            stats["rag_replied"] = cursor.fetchone()[0]

            cursor.execute(
                "SELECT COUNT(*) FROM emails WHERE status = ?",
                (EmailStatus.MANUAL_REQUIRED.value,)
            )
            stats["pending_manual"] = cursor.fetchone()[0]

            cursor.execute(
                "SELECT COUNT(*) FROM drafts WHERE status = 'pending'"
            )
            stats["drafts_pending"] = cursor.fetchone()[0]

            return stats


# Singleton instance
_database: Optional[Database] = None


def get_database() -> Database:
    """Get or create database instance."""
    global _database
    if _database is None:
        _database = Database()
    return _database
