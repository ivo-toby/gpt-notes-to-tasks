"""Service for managing the vector store using ChromaDB."""

import os
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class VectorStoreService:
    """Manages document storage and retrieval using ChromaDB."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the vector store service.

        Args:
            config: Configuration dictionary containing vector store settings
        """
        self.config = config.get('vector_store', {})
        self.db_path = os.path.expanduser(self.config.get('path', '~/Documents/notes/.vector_store'))
        os.makedirs(self.db_path, exist_ok=True)
        
        self.client = chromadb.PersistentClient(
            path=self.db_path,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        self.collection = self.client.get_or_create_collection(
            name="notes",
            metadata={"description": "Obsidian notes and their embeddings"}
        )

    def add_document(self, doc_id: str, chunks: List[str], embeddings: List[List[float]], 
                    metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Add a document's chunks and their embeddings to the store.

        Args:
            doc_id: Unique identifier for the document
            chunks: List of text chunks from the document
            embeddings: List of embedding vectors corresponding to chunks
            metadata: Optional metadata about the document
        """
        chunk_ids = [f"{doc_id}_chunk_{i}" for i in range(len(chunks))]
        chunk_metadata = [{
            "doc_id": doc_id,
            "chunk_index": i,
            **(metadata or {})
        } for i in range(len(chunks))]

        self.collection.add(
            ids=chunk_ids,
            embeddings=embeddings,
            documents=chunks,
            metadatas=chunk_metadata
        )
        logger.info(f"Added document {doc_id} with {len(chunks)} chunks to vector store")

    def find_similar(self, query_embedding: List[float], limit: int = 5, 
                    threshold: Optional[float] = None) -> List[Dict[str, Any]]:
        """
        Find similar documents based on embedding similarity.

        Args:
            query_embedding: The embedding vector to compare against
            limit: Maximum number of results to return
            threshold: Optional similarity threshold (0-1)

        Returns:
            List of similar documents with their metadata
        """
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=limit,
            include=["documents", "metadatas", "distances"]
        )

        # Format results
        similar_docs = []
        for i in range(len(results['ids'][0])):
            similarity = 1 - results['distances'][0][i]  # Convert distance to similarity
            if threshold and similarity < threshold:
                continue
                
            similar_docs.append({
                'chunk_id': results['ids'][0][i],
                'content': results['documents'][0][i],
                'metadata': results['metadatas'][0][i],
                'similarity': similarity
            })

        return similar_docs

    def update_document(self, doc_id: str, new_chunks: List[str], 
                       new_embeddings: List[List[float]], 
                       metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Update an existing document with new chunks and embeddings.

        Args:
            doc_id: Unique identifier for the document
            new_chunks: New list of text chunks
            new_embeddings: New list of embedding vectors
            metadata: Optional new metadata
        """
        # Remove existing chunks for this document
        self.collection.delete(
            where={"doc_id": doc_id}
        )
        
        # Add new chunks
        self.add_document(doc_id, new_chunks, new_embeddings, metadata)
        logger.info(f"Updated document {doc_id} with {len(new_chunks)} chunks")

    def get_document_chunks(self, doc_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve all chunks for a specific document.

        Args:
            doc_id: Unique identifier for the document

        Returns:
            List of chunks with their metadata
        """
        results = self.collection.get(
            where={"doc_id": doc_id},
            include=["documents", "metadatas"]
        )

        return [{
            'content': doc,
            'metadata': meta
        } for doc, meta in zip(results['documents'], results['metadatas'])]
