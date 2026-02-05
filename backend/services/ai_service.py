import google.generativeai as genai
from typing import Optional, List
import json

from config import GEMINI_API_KEY
from models.schemas import Email, EmailCategory, ClassificationResult


# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)


class AIService:
    def __init__(self):
        self.model = genai.GenerativeModel("gemini-2.5-flash")
        self.embedding_model = "models/embedding-001"

    def classify_email(self, email: Email) -> ClassificationResult:
        """Classify an email into one of four categories."""
        prompt = f"""Analyze this email and classify it into ONE of these categories:

1. AUTO_REPLY: Generic/simple messages that don't need company knowledge or verification.
   Examples: "Thank you", "OK", "Got it", "Noted", "Thanks for the info", simple acknowledgments.

2. RAG_REPLY: Questions about company information, products, policies, FAQs.
   Examples: "What are your business hours?", "How do I return a product?", "What's your refund policy?"

3. PENDING_MANUAL: Critical issues that REQUIRE human attention.
   Examples: Complaints, legal matters, refund requests, urgent issues, angry customers, threats.

4. DRAFT_REVIEW: Questions the AI can answer but should be verified by staff first.
   Examples: Complex product questions, pricing inquiries, partnership requests, custom orders.

EMAIL DETAILS:
From: {email.sender_name or email.sender}
Subject: {email.subject}
Body:
{email.body[:2000]}

Respond in this exact JSON format:
{{
    "category": "AUTO_REPLY" or "RAG_REPLY" or "PENDING_MANUAL" or "DRAFT_REVIEW",
    "confidence": 0.0 to 1.0,
    "reasoning": "Brief explanation of why this category was chosen"
}}

Only output the JSON, nothing else."""

        try:
            response = self.model.generate_content(prompt)
            result_text = response.text.strip()

            # Clean up response if needed
            if result_text.startswith("```json"):
                result_text = result_text[7:]
            if result_text.startswith("```"):
                result_text = result_text[3:]
            if result_text.endswith("```"):
                result_text = result_text[:-3]

            result = json.loads(result_text.strip())

            # Map category string to enum
            category_map = {
                "AUTO_REPLY": EmailCategory.AUTO_REPLY,
                "RAG_REPLY": EmailCategory.RAG_REPLY,
                "PENDING_MANUAL": EmailCategory.PENDING_MANUAL,
                "DRAFT_REVIEW": EmailCategory.DRAFT_REVIEW
            }

            return ClassificationResult(
                category=category_map.get(result["category"], EmailCategory.PENDING_MANUAL),
                confidence=float(result.get("confidence", 0.5)),
                reasoning=result.get("reasoning", "")
            )

        except Exception as e:
            print(f"Classification error: {e}")
            # Default to manual review if classification fails
            return ClassificationResult(
                category=EmailCategory.PENDING_MANUAL,
                confidence=0.0,
                reasoning=f"Classification failed: {str(e)}"
            )

    def generate_generic_reply(self, email: Email) -> str:
        """Generate a simple reply for generic emails."""
        prompt = f"""Generate a brief, polite response to this simple email.
Keep it professional but warm. 1-3 sentences max.

From: {email.sender_name or email.sender}
Subject: {email.subject}
Body: {email.body[:500]}

Just write the response body, no subject line or signature."""

        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Error generating generic reply: {e}")
            return "Thank you for your message. We appreciate you reaching out to us."

    def generate_rag_reply(self, email: Email, context: str) -> str:
        """Generate a reply using RAG context."""
        prompt = f"""You are a helpful customer service representative.
Use the provided company knowledge to answer the customer's question.
Be professional, accurate, and helpful.

CUSTOMER EMAIL:
From: {email.sender_name or email.sender}
Subject: {email.subject}
Question: {email.body[:1500]}

COMPANY KNOWLEDGE BASE CONTEXT:
{context}

Instructions:
- Answer based ONLY on the provided context
- If the context doesn't contain relevant information, say you'll forward to the appropriate team
- Be concise but complete
- End with an offer to help further

Write only the response body:"""

        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Error generating RAG reply: {e}")
            return "Thank you for your question. Let me connect you with our team who can provide more detailed information."

    def generate_draft_reply(self, email: Email, context: Optional[str] = None) -> str:
        """Generate a draft reply for review."""
        context_section = ""
        if context:
            context_section = f"""
AVAILABLE COMPANY INFORMATION:
{context}
"""

        prompt = f"""Generate a professional response to this customer email.
This will be reviewed by staff before sending, so be thorough but accurate.

CUSTOMER EMAIL:
From: {email.sender_name or email.sender}
Subject: {email.subject}
Body: {email.body[:2000]}
{context_section}

Instructions:
- Write a complete, professional response
- If you're unsure about specific details, indicate [VERIFY: detail to verify]
- Be helpful and offer to assist further
- Use a professional but friendly tone

Write only the response body:"""

        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Error generating draft reply: {e}")
            return "[Draft generation failed. Please compose manually.]"

    def get_embeddings(self, text: str) -> List[float]:
        """Generate embeddings for text using Gemini."""
        try:
            result = genai.embed_content(
                model=self.embedding_model,
                content=text,
                task_type="retrieval_document"
            )
            return result["embedding"]
        except Exception as e:
            print(f"Error generating embeddings: {e}")
            return []

    def get_query_embeddings(self, query: str) -> List[float]:
        """Generate embeddings for a query."""
        try:
            result = genai.embed_content(
                model=self.embedding_model,
                content=query,
                task_type="retrieval_query"
            )
            return result["embedding"]
        except Exception as e:
            print(f"Error generating query embeddings: {e}")
            return []


# Singleton instance
_ai_service: Optional[AIService] = None


def get_ai_service() -> AIService:
    """Get or create AI service instance."""
    global _ai_service
    if _ai_service is None:
        _ai_service = AIService()
    return _ai_service
