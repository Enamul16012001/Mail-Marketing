import os
import uuid
from pathlib import Path
from typing import List, Optional, Dict, Any
import chromadb
import PyPDF2
from docx import Document
import json

from config import CHROMA_PERSIST_DIR, KNOWLEDGE_BASE_DIR
from services.ai_service import get_ai_service


class RAGService:
    """RAG pipeline using ChromaDB for vector storage."""

    def __init__(self):
        self.ai_service = get_ai_service()

        # Initialize ChromaDB with persistence (compatible with newer versions)
        os.makedirs(CHROMA_PERSIST_DIR, exist_ok=True)
        self.client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name="knowledge_base",
            metadata={"description": "Company knowledge base documents"}
        )

        # Track files metadata
        self.metadata_file = Path(CHROMA_PERSIST_DIR) / "files_metadata.json"
        self.files_metadata = self._load_metadata()

    def _load_metadata(self) -> Dict[str, Any]:
        """Load files metadata from disk."""
        if self.metadata_file.exists():
            with open(self.metadata_file, "r") as f:
                return json.load(f)
        return {}

    def _save_metadata(self):
        """Save files metadata to disk."""
        os.makedirs(os.path.dirname(self.metadata_file), exist_ok=True)
        with open(self.metadata_file, "w") as f:
            json.dump(self.files_metadata, f, indent=2)

    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF file."""
        text = ""
        try:
            with open(file_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text += page.extract_text() + "\n"
        except Exception as e:
            print(f"Error extracting PDF: {e}")
        return text.strip()

    def extract_text_from_docx(self, file_path: str) -> str:
        """Extract text from DOCX file."""
        text = ""
        try:
            doc = Document(file_path)
            for para in doc.paragraphs:
                text += para.text + "\n"
        except Exception as e:
            print(f"Error extracting DOCX: {e}")
        return text.strip()

    def extract_text_from_txt(self, file_path: str) -> str:
        """Extract text from TXT file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception as e:
            print(f"Error reading TXT: {e}")
            return ""

    def extract_text(self, file_path: str) -> str:
        """Extract text based on file type."""
        ext = Path(file_path).suffix.lower()

        if ext == ".pdf":
            return self.extract_text_from_pdf(file_path)
        elif ext in [".docx", ".doc"]:
            return self.extract_text_from_docx(file_path)
        elif ext == ".txt":
            return self.extract_text_from_txt(file_path)
        else:
            # Try as plain text
            return self.extract_text_from_txt(file_path)

    def chunk_text(
        self,
        text: str,
        chunk_size: int = 500,
        overlap: int = 50
    ) -> List[str]:
        """Split text into overlapping chunks."""
        if not text:
            return []

        words = text.split()
        chunks = []

        for i in range(0, len(words), chunk_size - overlap):
            chunk = " ".join(words[i:i + chunk_size])
            if chunk.strip():
                chunks.append(chunk)

        return chunks

    def add_document(self, file_path: str, filename: str) -> Dict[str, Any]:
        """Add a document to the knowledge base."""
        file_id = str(uuid.uuid4())

        # Extract text
        text = self.extract_text(file_path)
        if not text:
            raise ValueError(f"Could not extract text from {filename}")

        # Chunk text
        chunks = self.chunk_text(text)

        # Generate embeddings and add to ChromaDB
        chunk_ids = []
        for i, chunk in enumerate(chunks):
            chunk_id = f"{file_id}_chunk_{i}"
            chunk_ids.append(chunk_id)

            # Get embeddings from AI service
            embeddings = self.ai_service.get_embeddings(chunk)

            self.collection.add(
                ids=[chunk_id],
                embeddings=[embeddings] if embeddings else None,
                documents=[chunk],
                metadatas=[{
                    "file_id": file_id,
                    "filename": filename,
                    "chunk_index": i,
                    "total_chunks": len(chunks)
                }]
            )

        # Save file metadata
        file_info = {
            "id": file_id,
            "filename": filename,
            "file_type": Path(filename).suffix.lower(),
            "file_size": os.path.getsize(file_path),
            "chunk_count": len(chunks),
            "chunk_ids": chunk_ids
        }
        self.files_metadata[file_id] = file_info
        self._save_metadata()

        return file_info

    def delete_document(self, file_id: str) -> bool:
        """Delete a document and its chunks from the knowledge base."""
        if file_id not in self.files_metadata:
            return False

        file_info = self.files_metadata[file_id]

        # Delete chunks from ChromaDB
        try:
            self.collection.delete(ids=file_info["chunk_ids"])
        except Exception as e:
            print(f"Error deleting chunks: {e}")

        # Delete from metadata
        del self.files_metadata[file_id]
        self._save_metadata()

        # Delete file from knowledge_base folder
        file_path = KNOWLEDGE_BASE_DIR / file_info["filename"]
        if file_path.exists():
            os.remove(file_path)

        return True

    def search(self, query: str, n_results: int = 5) -> str:
        """Search knowledge base and return relevant context."""
        if self.collection.count() == 0:
            return "No knowledge base documents available."

        try:
            # Get query embeddings
            query_embedding = self.ai_service.get_query_embeddings(query)

            if query_embedding:
                results = self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=n_results
                )
            else:
                # Fallback to text search
                results = self.collection.query(
                    query_texts=[query],
                    n_results=n_results
                )

            # Format results
            documents = results.get("documents", [[]])[0]
            metadatas = results.get("metadatas", [[]])[0]

            if not documents:
                return "No relevant information found in knowledge base."

            context_parts = []
            for doc, meta in zip(documents, metadatas):
                source = meta.get("filename", "Unknown")
                context_parts.append(f"[Source: {source}]\n{doc}")

            return "\n\n---\n\n".join(context_parts)

        except Exception as e:
            print(f"Search error: {e}")
            return "Error searching knowledge base."

    def list_files(self) -> List[Dict[str, Any]]:
        """List all files in the knowledge base."""
        return list(self.files_metadata.values())

    def get_stats(self) -> Dict[str, int]:
        """Get knowledge base statistics."""
        return {
            "total_files": len(self.files_metadata),
            "total_chunks": self.collection.count()
        }


# Singleton instance
_rag_service: Optional[RAGService] = None


def get_rag_service() -> RAGService:
    """Get or create RAG service instance."""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service
