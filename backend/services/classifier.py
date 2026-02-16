from typing import Tuple, Optional

from models.schemas import Email, EmailCategory, ClassificationResult
from services.ai_service import get_ai_service
from services.rag_service import get_rag_service


class EmailClassifier:
    """Handles email classification and response generation."""

    def __init__(self):
        self.ai_service = get_ai_service()
        self.rag_service = get_rag_service()

    def process_email(self, email: Email, thread_history: str = "") -> Tuple[ClassificationResult, Optional[str]]:
        """
        Process an email: classify it and generate appropriate response.

        Returns:
            Tuple of (classification_result, generated_response)
        """
        # Step 1: Classify the email (with thread context)
        classification = self.ai_service.classify_email(email, thread_history)

        # Step 2: Generate response based on category
        response = None

        if classification.category == EmailCategory.AUTO_REPLY:
            response = self.ai_service.generate_generic_reply(email, thread_history)

        elif classification.category == EmailCategory.RAG_REPLY:
            context = self.rag_service.search(email.body + " " + email.subject)
            response = self.ai_service.generate_rag_reply(email, context, thread_history)

        elif classification.category == EmailCategory.DRAFT_REVIEW:
            context = self.rag_service.search(email.body + " " + email.subject)
            response = self.ai_service.generate_draft_reply(email, context, thread_history)

        elif classification.category == EmailCategory.PENDING_MANUAL:
            response = None

        return classification, response

    def regenerate_response(
        self,
        email: Email,
        category: EmailCategory,
        additional_context: Optional[str] = None
    ) -> str:
        """Regenerate a response for an email with optional additional context."""

        if category == EmailCategory.AUTO_REPLY:
            return self.ai_service.generate_generic_reply(email)

        elif category == EmailCategory.RAG_REPLY:
            context = self.rag_service.search(email.body + " " + email.subject)
            if additional_context:
                context = f"{context}\n\nAdditional context:\n{additional_context}"
            return self.ai_service.generate_rag_reply(email, context)

        elif category == EmailCategory.DRAFT_REVIEW:
            context = self.rag_service.search(email.body + " " + email.subject)
            if additional_context:
                context = f"{context}\n\nAdditional context:\n{additional_context}"
            return self.ai_service.generate_draft_reply(email, context)

        return ""


# Singleton instance
_classifier: Optional[EmailClassifier] = None


def get_classifier() -> EmailClassifier:
    """Get or create classifier instance."""
    global _classifier
    if _classifier is None:
        _classifier = EmailClassifier()
    return _classifier
