"""
RAG (Retrieval-Augmented Generation) Service
Implements document retrieval and question answering
Future: RAPTOR hierarchical retrieval
"""

from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
import logging
from pathlib import Path

from app.config import settings
from app.utils.llm_client import llm_client
from app.database.sqlite_manager import db_manager

logger = logging.getLogger(__name__)


class RAGService:
    """Service for RAG-based document retrieval and QA"""

    def __init__(self):
        self.embedding_model_name = settings.EMBEDDING_MODEL
        self.embedding_model = None
        self.vector_db_path = Path(settings.VECTOR_DB_PATH)
        self.chroma_client = None
        self.collection = None
        self.chunk_size = settings.CHUNK_SIZE
        self.chunk_overlap = settings.CHUNK_OVERLAP

    async def initialize(self):
        """Initialize embedding model and vector database"""
        try:
            # Load embedding model
            self.embedding_model = SentenceTransformer(self.embedding_model_name)
            logger.info(f"Loaded embedding model: {self.embedding_model_name}")

            # Initialize ChromaDB
            self.chroma_client = chromadb.PersistentClient(
                path=str(self.vector_db_path),
                settings=Settings(anonymized_telemetry=False)
            )

            # Get or create collection
            self.collection = self.chroma_client.get_or_create_collection(
                name="sec_filings",
                metadata={"description": "SEC filing documents"}
            )

            logger.info("RAG service initialized")

        except Exception as e:
            logger.error(f"Error initializing RAG service: {e}")
            raise

    def chunk_text(self, text: str) -> List[str]:
        """
        Chunk text into smaller segments

        TODO: Enhance with RAPTOR hierarchical chunking
        """
        if not text:
            return []

        chunks = []
        words = text.split()

        for i in range(0, len(words), self.chunk_size - self.chunk_overlap):
            chunk = ' '.join(words[i:i + self.chunk_size])
            if chunk:
                chunks.append(chunk)

        return chunks

    async def index_document(
        self,
        doc_id: str,
        text: str,
        metadata: Dict[str, Any]
    ):
        """
        Index a document into the vector database

        Args:
            doc_id: Unique document identifier
            text: Document text
            metadata: Document metadata (ticker, filing_type, date, etc.)
        """
        try:
            if not self.collection:
                await self.initialize()

            # Chunk the document
            chunks = self.chunk_text(text)

            if not chunks:
                logger.warning(f"No chunks generated for doc {doc_id}")
                return

            # Generate embeddings
            embeddings = self.embedding_model.encode(chunks).tolist()

            # Prepare for insertion
            ids = [f"{doc_id}_chunk_{i}" for i in range(len(chunks))]
            metadatas = [{**metadata, 'chunk_index': i} for i in range(len(chunks))]

            # Insert into ChromaDB
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=chunks,
                metadatas=metadatas
            )

            logger.info(f"Indexed document {doc_id} with {len(chunks)} chunks")

        except Exception as e:
            logger.error(f"Error indexing document {doc_id}: {e}")

    async def retrieve_relevant_chunks(
        self,
        query: str,
        ticker: Optional[str] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant document chunks for a query

        TODO: Implement RAPTOR multi-level retrieval
        """
        try:
            if not self.collection:
                await self.initialize()

            # Generate query embedding
            query_embedding = self.embedding_model.encode([query])[0].tolist()

            # Build filter
            where_filter = {'ticker': ticker} if ticker else None

            # Query ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where_filter
            )

            # Format results
            chunks = []
            if results['documents']:
                for i, doc in enumerate(results['documents'][0]):
                    chunks.append({
                        'text': doc,
                        'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                        'distance': results['distances'][0][i] if results['distances'] else None
                    })

            logger.info(f"Retrieved {len(chunks)} chunks for query: {query[:50]}...")
            return chunks

        except Exception as e:
            logger.error(f"Error retrieving chunks: {e}")
            return []

    async def answer_question(
        self,
        question: str,
        ticker: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Answer a question using RAG

        Args:
            question: User question
            ticker: Optional ticker to filter documents

        Returns:
            Answer and source documents
        """
        try:
            # Retrieve relevant chunks
            chunks = await self.retrieve_relevant_chunks(question, ticker=ticker, top_k=5)

            if not chunks:
                return {
                    'answer': "I don't have enough information to answer that question.",
                    'sources': [],
                    'confidence': 0.0
                }

            # Build context from chunks
            context = "\n\n".join([chunk['text'] for chunk in chunks])

            # Generate answer using LLM
            answer = await llm_client.answer_query(question, context)

            # Format response
            return {
                'answer': answer,
                'sources': [chunk['metadata'] for chunk in chunks],
                'confidence': 0.8  # Placeholder - can be enhanced
            }

        except Exception as e:
            logger.error(f"Error answering question: {e}")
            return {
                'answer': f"Error: {str(e)}",
                'sources': [],
                'confidence': 0.0
            }

    async def index_sec_filings_for_ticker(self, ticker: str):
        """Index all SEC filings for a ticker"""
        try:
            # Fetch filings from database
            # Note: This assumes filings are already in the database
            # You would query the sec_filings table here

            logger.info(f"Indexing SEC filings for {ticker}")

            # TODO: Fetch from database and index
            # For now, this is a placeholder

        except Exception as e:
            logger.error(f"Error indexing filings for {ticker}: {e}")


# Global instance
rag_service = RAGService()
