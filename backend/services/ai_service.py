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
        self.embedding_model = "models/gemini-embedding-001"

    def classify_email(self, email: Email, thread_history: str = "") -> ClassificationResult:
        """Classify an email into one of four categories."""
        thread_section = ""
        if thread_history:
            thread_section = f"""
PREVIOUS CONVERSATION IN THIS THREAD:
{thread_history[:3000]}

---
"""

        prompt = f"""Analyze this email and classify it into ONE of these categories:

1. AUTO_REPLY: Generic/simple messages, general knowledge questions, or anything answerable from the conversation history alone.
   Examples: "Thank you", "OK", "Got it", simple acknowledgments, "What did we discuss?", "What was our previous conversation?", general knowledge questions like "What is the capital of France?"

2. RAG_REPLY: Questions specifically about THIS COMPANY's information, products, services, or policies that require company knowledge base lookup.
   Examples: "What are your business hours?", "How do I return a product?", "What's your refund policy?"

3. PENDING_MANUAL: Critical issues that REQUIRE human attention.
   Examples: Complaints, legal matters, refund requests, urgent issues, angry customers, threats.

4. DRAFT_REVIEW: Questions the AI can answer but should be verified by staff first.
   Examples: Complex product questions, pricing inquiries, partnership requests, custom orders.
{thread_section}
LATEST EMAIL (classify this one):
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

            # Extract JSON from response (handle markdown wrapping)
            import re as _re
            json_match = _re.search(r'\{[^{}]*\}', result_text, _re.DOTALL)
            if json_match:
                result_text = json_match.group()

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

    def generate_generic_reply(self, email: Email, thread_history: str = "") -> str:
        """Generate a simple reply for generic emails."""
        thread_section = ""
        if thread_history:
            thread_section = f"""
PREVIOUS CONVERSATION:
{thread_history[:2000]}

---
"""

        prompt = f"""Generate a brief, polite response to this simple email.
Keep it professional but warm. 1-3 sentences max.
Write in plain text only — no markdown formatting, no bold, no bullet points.
{thread_section}
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

    def generate_rag_reply(self, email: Email, context: str, thread_history: str = "") -> str:
        """Generate a reply using RAG context."""
        thread_section = ""
        if thread_history:
            thread_section = f"""
PREVIOUS CONVERSATION IN THIS THREAD:
{thread_history[:3000]}

---
"""

        prompt = f"""You are a helpful customer service representative.
Use the provided company knowledge to answer the customer's question.
Be professional, accurate, and helpful.
{thread_section}
CUSTOMER EMAIL:
From: {email.sender_name or email.sender}
Subject: {email.subject}
Question: {email.body[:1500]}

COMPANY KNOWLEDGE BASE CONTEXT:
{context}

Instructions:
- If the provided context contains relevant information, use it to answer
- If the context is NOT relevant but you can confidently answer the question from general knowledge, go ahead and answer it directly
- Only say you'll forward to the appropriate team if the question is company-specific and you truly cannot answer it
- Be concise but complete
- End with an offer to help further
- Write in plain text only — no markdown formatting, no bold (**), no bullet points (- or *)
- Use natural paragraph breaks instead of lists

Write only the response body:"""

        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Error generating RAG reply: {e}")
            return "Thank you for your question. Let me connect you with our team who can provide more detailed information."

    def generate_draft_reply(self, email: Email, context: Optional[str] = None, thread_history: str = "") -> str:
        """Generate a draft reply for review."""
        context_section = ""
        if context:
            context_section = f"""
AVAILABLE COMPANY INFORMATION:
{context}
"""
        thread_section = ""
        if thread_history:
            thread_section = f"""
PREVIOUS CONVERSATION IN THIS THREAD:
{thread_history[:3000]}

---
"""

        prompt = f"""Generate a professional response to this customer email.
This will be reviewed by staff before sending, so be thorough but accurate.
{thread_section}
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
- Write in plain text only — no markdown formatting, no bold (**), no bullet points (- or *)

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
