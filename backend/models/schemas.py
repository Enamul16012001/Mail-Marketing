from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum


class EmailCategory(str, Enum):
    AUTO_REPLY = "auto_reply"
    RAG_REPLY = "rag_reply"
    PENDING_MANUAL = "pending_manual"
    DRAFT_REVIEW = "draft_review"


class EmailStatus(str, Enum):
    PENDING = "pending"
    REPLIED = "replied"
    DRAFT = "draft"
    MANUAL_REQUIRED = "manual_required"


class EmailAttachment(BaseModel):
    filename: str
    mime_type: str
    size: int
    content: Optional[str] = None  # Base64 encoded for small files


class Email(BaseModel):
    id: str
    thread_id: str
    sender: str
    sender_name: Optional[str] = None
    recipient: str
    subject: str
    body: str
    body_html: Optional[str] = None
    attachments: List[EmailAttachment] = []
    received_at: datetime
    category: Optional[EmailCategory] = None
    status: EmailStatus = EmailStatus.PENDING
    ai_response: Optional[str] = None
    processed_at: Optional[datetime] = None


class EmailReply(BaseModel):
    to: str
    subject: str
    body: str
    thread_id: Optional[str] = None
    message_id: Optional[str] = None  # For replying to specific message


class ComposeEmail(BaseModel):
    to: List[str]  # Multiple recipients
    cc: List[str] = []  # CC recipients
    bcc: List[str] = []  # BCC recipients
    subject: str
    body: str


class Draft(BaseModel):
    id: str
    email_id: str
    original_email: Email
    ai_response: str
    created_at: datetime
    status: str = "pending"  # pending, approved, discarded


class DraftEdit(BaseModel):
    content: str


class KnowledgeFile(BaseModel):
    id: str
    filename: str
    file_type: str
    file_size: int
    chunk_count: int
    uploaded_at: datetime


class ClassificationResult(BaseModel):
    category: EmailCategory
    confidence: float
    reasoning: str
    suggested_response: Optional[str] = None


class StatsResponse(BaseModel):
    total_emails_processed: int
    auto_replied: int
    rag_replied: int
    pending_manual: int
    drafts_pending: int
    knowledge_files: int


class SettingsUpdate(BaseModel):
    polling_interval: Optional[int] = None
    auto_reply_enabled: Optional[bool] = None
