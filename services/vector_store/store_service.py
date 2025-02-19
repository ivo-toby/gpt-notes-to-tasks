"""Service for managing the vector store using ChromaDB."""

import json
import logging
import os
import time
import numpy as np
from sqlite3 import OperationalError
from typing import Any, Dict, List, Optional

import chromadb
from chromadb.config import Settings

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds


class VectorStoreService:
    """Manages document storage and retrieval using ChromaDB."""

    def __init__(
        self, config: Dict[str, Any], chunking_service=None, embedding_service=None
    ):
        """
        Initialize the vector store service.

        Args:
            config: Configuration dictionary containing vector store settings
            chunking_service: Optional ChunkingService instance
            embedding_service: Optional EmbeddingService instance
        """
        self.config = config.get("vector_store", {})
        self.chunking_service = chunking_service
        self.embedding_service = embedding_service
        self.db_path = os.path.expanduser(
            self.config.get("path", "~/Documents/notes/.vector_store")
        )
        os.makedirs(self.db_path, exist_ok=True)

        # Get embedding dimensions from the model
        self.embedding_dims = self._get_embedding_dimensions()
        logger.info(f"Using embedding dimensions: {self.embedding_dims}")

        # Get HNSW settings from config
        hnsw_config = self.config.get("hnsw_config", {})

        # Initialize ChromaDB with settings
        self.client = chromadb.PersistentClient(
            path=self.db_path,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True,
                persist_directory=self.db_path,
            ),
        )

        # Configure collection settings with HNSW parameters
        collection_params = {
            "hnsw:space": "cosine",  # Use cosine distance
            "hnsw:construction_ef": hnsw_config.get("ef_construction", 400),
            "hnsw:search_ef": hnsw_config.get("ef_search", 200),
            "hnsw:M": hnsw_config.get("m", 128),
        }

        # Initialize system metadata collection
        self.system_collection = self.client.get_or_create_collection(
            name="system",
            metadata={
                "description": "System-level metadata and tracking",
                **collection_params
            },
        )

        # Create metadata collection for tracking document updates
        self.metadata_collection = self.client.get_or_create_collection(
            name="metadata",
            metadata={
                "description": "Document metadata and update tracking",
                **collection_params
            },
        )

        # Create collections for different types of content
        try:
            self.collections = {
                "notes": self.client.get_or_create_collection(
                    name="notes",
                    metadata={
                        "description": "General notes and their chunks",
                        **collection_params
                    },
                ),
                "links": self.client.get_or_create_collection(
                    name="links",
                    metadata={
                        "description": "Link relationships between notes",
                        **collection_params
                    },
                ),
                "references": self.client.get_or_create_collection(
                    name="references",
                    metadata={
                        "description": "External references and citations",
                        **collection_params
                    },
                ),
            }
            logger.info("Vector store collections initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing vector store collections: {str(e)}")
            raise

    def clear_all_collections(self) -> None:
        """Clear all data from all collections by deleting and recreating them."""
        try:
            logger.info("Clearing all collections...")
            
            # Delete and recreate each collection
            for name, old_collection in self.collections.items():
                collection_metadata = old_collection.metadata
                self.client.delete_collection(name)
                self.collections[name] = self.client.create_collection(
                    name=name,
                    metadata=collection_metadata
                )
                logger.info(f"Cleared collection: {name}")
            
            # Handle system and metadata collections
            self.client.delete_collection("system")
            self.client.delete_collection("metadata")
            
            # Recreate system and metadata collections with original settings
            self.system_collection = self.client.create_collection(
                name="system",
                metadata={"description": "System-level metadata and tracking"}
            )
            self.metadata_collection = self.client.create_collection(
                name="metadata",
                metadata={"description": "Document metadata and update tracking"}
            )
            
            logger.info("Successfully cleared and recreated all collections")
        except Exception as e:
            logger.error(f"Error clearing collections: {str(e)}")
            raise

    def get_last_update_time(self) -> float:
        """Get the timestamp of the last update operation."""
        try:
            results = self.system_collection.get(
                ids=["last_update"], include=["metadatas"]
            )
            if results["ids"]:
                return float(results["metadatas"][0].get("timestamp", 0))
            return 0
        except Exception as e:
            logger.error(f"Error getting last update time: {str(e)}")
            return 0

    def set_last_update_time(self, timestamp: float) -> None:
        """Set the timestamp of the last update operation."""
        try:
            self._retry_operation(
                self.system_collection.upsert,
                ids=["last_update"],
                metadatas=[{"timestamp": str(timestamp)}],
                embeddings=[[1.0] * self.embedding_dims],
                documents=[""],
            )
        except Exception as e:
            logger.error(f"Error setting last update time: {str(e)}")

    def needs_update(self, doc_id: str, modified_time: float) -> bool:
        """
        Check if a document needs to be updated in the vector store.

        Args:
            doc_id: Document ID to check
            modified_time: Last modification timestamp of the document

        Returns:
            bool: True if document needs updating, False otherwise
        """
        try:
            # Check if document exists in metadata collection
            results = self.metadata_collection.get(ids=[doc_id], include=["metadatas"])

            if not results["ids"]:
                return True  # Document not in store, needs to be added

            stored_time = results["metadatas"][0].get("modified_time", 0)
            return modified_time > stored_time
        except Exception as e:
            logger.error(f"Error checking document update status: {str(e)}")
            return True  # If in doubt, update the document

    def _retry_operation(self, operation, *args, **kwargs):
        """Execute an operation with retries."""
        last_error = None
        for attempt in range(MAX_RETRIES):
            try:
                return operation(*args, **kwargs)
            except OperationalError as e:
                last_error = e
                logger.warning(
                    f"Database operation failed (attempt {attempt + 1}/{MAX_RETRIES}): {str(e)}"
                )
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY * (attempt + 1))
                continue
            except Exception as e:
                logger.error(f"Unexpected error during database operation: {str(e)}")
                raise

        logger.error(f"Operation failed after {MAX_RETRIES} attempts")
        raise last_error

    def add_document(
        self,
        doc_id: str,
        chunks: List[str],
        embeddings: List[List[float]],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Add a document's chunks and their embeddings to the store.

        Args:
            doc_id: Unique identifier for the document
            chunks: List of text chunks from the document
            embeddings: List of embedding vectors corresponding to chunks
            metadata: Optional metadata about the document
        """
        # Ensure metadata exists
        metadata = metadata or {}

        # Create chunk IDs and metadata
        chunk_ids = []
        chunk_metadata = []

        for i, chunk in enumerate(chunks):
            chunk_id = f"{doc_id}_chunk_{i}"
            # Ensure all metadata values are valid types
            chunk_meta = {
                "doc_id": doc_id,
                "chunk_index": i,
                "doc_type": metadata.get("type", "note"),
                "source_path": metadata.get("source", ""),
                "date": metadata.get("date", "") or "",
                "filename": metadata.get("filename", "") or "",
            }

            # Extract links if present in the chunk
            wiki_links = self._extract_wiki_links(chunk)
            if wiki_links:
                chunk_meta["wiki_links"] = json.dumps(wiki_links)

            # Extract external references if present
            external_refs = self._extract_external_refs(chunk)
            if external_refs:
                chunk_meta["external_refs"] = json.dumps(external_refs)

            chunk_ids.append(chunk_id)
            chunk_metadata.append(chunk_meta)

        # Only add if we have chunks
        if chunk_ids:
            # Upsert chunks to main notes collection
            self._retry_operation(
                self.collections["notes"].upsert,
                ids=chunk_ids,
                embeddings=embeddings,
                documents=chunks,
                metadatas=chunk_metadata,
            )
            logger.info(f"Upserted {len(chunk_ids)} chunks to vector store")
        else:
            logger.warning(f"No valid chunks to add for document {doc_id}")

        # Store link relationships
        self._store_link_relationships(doc_id, chunks, metadata)

        # Store document metadata for update tracking
        if metadata and "modified_time" in metadata:
            self._retry_operation(
                self.metadata_collection.upsert,
                ids=[doc_id],
                metadatas=[{"modified_time": metadata["modified_time"]}],
                embeddings=[
                    [1.0] * self.embedding_dims
                ],  # Dummy embedding for metadata tracking
                documents=[""],  # Empty document as it's just for tracking
            )

        logger.info(
            f"Added document {doc_id} with {len(chunks)} chunks to vector store"
        )

    def find_similar(
        self,
        query_embedding: List[float],
        limit: int = 5,
        threshold: Optional[float] = None,
        doc_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Find similar documents based on embedding similarity.

        Args:
            query_embedding: The embedding vector to compare against
            limit: Maximum number of results to return
            threshold: Optional similarity threshold (-1 to 1, where 1 is most similar)
            doc_type: Optional filter for specific document types

        Returns:
            List of similar documents with their metadata
        """
        try:
            # Prepare where clause if doc_type is specified
            where = {"doc_type": doc_type} if doc_type else None

            logger.info(
                f"Searching for similar documents with limit={limit}"
                + (f", doc_type={doc_type}" if doc_type else "")
            )

            # Add debug info about query embedding
            import numpy as np
            query_norm = np.linalg.norm(query_embedding)
            logger.debug(f"Query embedding norm: {query_norm}")

            # Debug query information
            import numpy as np
            query_norm = np.linalg.norm(query_embedding)
            logger.debug(f"Query vector norm: {query_norm}")

            # Execute query
            logger.debug(f"Executing query with limit={limit} and doc_type={doc_type}")
            results = self.collections["notes"].query(
                query_embeddings=[query_embedding],
                n_results=limit,
                where=where,
                include=["documents", "metadatas", "distances", "embeddings"],
            )

            if not results["ids"][0]:
                logger.info("No matching documents found")
                return []

            logger.info(f"Found {len(results['ids'][0])} matching documents")
            logger.debug("Processing results...")

            # Format results
            similar_docs = []
            for i in range(len(results["ids"][0])):
                # Get embedding and analyze
                doc_embedding = np.array(results["embeddings"][0][i])
                doc_norm = np.linalg.norm(doc_embedding)
                dot_product = np.dot(query_embedding, doc_embedding)
                raw_distance = results["distances"][0][i]
                similarity = 1 - raw_distance

                logger.debug(f"Document {i}:")
                logger.debug(f"  - Norm: {doc_norm}")
                logger.debug(f"  - Dot product with query: {dot_product}")
                logger.debug(f"  - Raw distance: {raw_distance}")
                logger.debug(f"  - Calculated similarity: {similarity}")
                logger.debug(f"  - Preview: {results['documents'][0][i][:100]}")
                logger.debug(f"Raw distance: {raw_distance}, Converted similarity: {similarity}")
                logger.debug(f"Document content preview: {results['documents'][0][i][:100]}...")
                if threshold and similarity < threshold:
                    logger.info(
                        f"Skipping result with similarity {similarity:.3f} below threshold {threshold}"
                    )
                    continue
                logger.debug(f"Including result with similarity {similarity:.3f}")

                metadata = results["metadatas"][0][i]
                # Parse stored JSON fields
                try:
                    if "wiki_links" in metadata and metadata["wiki_links"]:
                        metadata["wiki_links"] = json.loads(metadata["wiki_links"])
                    if "external_refs" in metadata and metadata["external_refs"]:
                        metadata["external_refs"] = json.loads(
                            metadata["external_refs"]
                        )
                except json.JSONDecodeError as e:
                    logger.warning(f"Error parsing JSON fields in metadata: {e}")

                similar_docs.append(
                    {
                        "chunk_id": results["ids"][0][i],
                        "content": results["documents"][0][i],
                        "metadata": metadata,
                        "similarity": similarity,
                    }
                )

            logger.info(f"Returning {len(similar_docs)} results after filtering")
            return similar_docs

        except Exception as e:
            logger.error(f"Error finding similar documents: {str(e)}")
            return []

    def find_connected_notes(self, doc_id: str) -> List[Dict[str, Any]]:
        """
        Find notes that are connected to the given document through links.

        Args:
            doc_id: Document ID to find connections for

        Returns:
            List of connected documents with their relationship info
        """
        # Query the links collection
        results = self.collections["links"].query(
            query_embeddings=[
                [1.0] * self.embedding_dims
            ],  # Dummy embedding for exact match
            where={"source_id": doc_id},
            include=["metadatas"],
        )

        connected_docs = []
        for metadata in results["metadatas"][0]:
            connected_docs.append(
                {
                    "target_id": metadata["target_id"],
                    "relationship": metadata.get("relationship", "linked"),
                    "link_type": metadata.get("link_type", "wiki"),
                    "context": metadata.get("context", ""),
                }
            )

        return connected_docs

    def find_backlinks(self, doc_id: str) -> List[Dict[str, Any]]:
        """
        Find all notes that link to the given document.

        Args:
            doc_id: Document ID to find backlinks for

        Returns:
            List of documents linking to this document
        """
        results = self.collections["links"].query(
            query_embeddings=[
                [1.0] * self.embedding_dims
            ],  # Dummy embedding for exact match
            where={"target_id": doc_id},
            include=["metadatas"],
        )

        backlinks = []
        for metadata in results["metadatas"][0]:
            backlinks.append(
                {
                    "source_id": metadata["source_id"],
                    "relationship": metadata.get("relationship", "linked"),
                    "link_type": metadata.get("link_type", "wiki"),
                    "context": metadata.get("context", ""),
                }
            )

        return backlinks

    def get_note_content(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the content and metadata for a specific note.

        Args:
            doc_id: Document ID to retrieve

        Returns:
            Dictionary containing note content and metadata, or None if not found
        """
        try:
            logger.info(f"Retrieving content for note: {doc_id}")
            # First try exact match on doc_id
            results = self.collections["notes"].query(
                query_embeddings=[[1.0] * self.embedding_dims],  # Dummy embedding for exact match
                where={"doc_id": doc_id},
                include=["documents", "metadatas", "embeddings"],
            )

            if not results["ids"][0]:
                logger.warning(f"No content found for note: {doc_id}")
                # Try searching by chunk IDs
                chunk_results = self.collections["notes"].get(
                    ids=[f"{doc_id}_chunk_0"],
                    include=["documents", "metadatas", "embeddings"],
                )
                if chunk_results["ids"]:
                    logger.info(f"Found content via chunk ID for note: {doc_id}")
                    return {
                        "content": chunk_results["documents"][0],
                        "metadata": chunk_results["metadatas"][0],
                        "embedding": chunk_results["embeddings"][0],
                    }
                logger.error(f"Note not found in vector store: {doc_id}")
                return None

            return {
                "content": results["documents"][0][0],
                "metadata": results["metadatas"][0][0],
                "embedding": results["embeddings"][0][0],
            }
        except Exception as e:
            logger.error(f"Error retrieving note content: {str(e)}")
            return None

    def update_document(
        self,
        doc_id: str,
        new_chunks: List[str],
        new_embeddings: List[List[float]],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Update an existing document with new chunks and embeddings.

        Args:
            doc_id: Unique identifier for the document
            new_chunks: New list of text chunks
            new_embeddings: New list of embedding vectors
            metadata: Optional new metadata
        """
        try:
            # Remove existing chunks for this document
            self._retry_operation(
                self.collections["notes"].delete, where={"doc_id": doc_id}
            )

            # Remove existing link relationships
            self._retry_operation(
                self.collections["links"].delete, where={"source_id": doc_id}
            )

            # Add new chunks and update metadata
            if metadata is None:
                try:
                    # Preserve existing metadata if not provided
                    existing_meta = self.metadata_collection.get(
                        ids=[doc_id], include=["metadatas"]
                    )
                    metadata = (existing_meta.get("metadatas", [{}])[0] 
                              if existing_meta and existing_meta.get("ids") 
                              else {})
                except Exception as e:
                    logger.warning(f"Error retrieving existing metadata for {doc_id}: {str(e)}")
                    metadata = {}

            # Update modification time
            metadata["modified_time"] = time.time()

            # Add new chunks
            self.add_document(doc_id, new_chunks, new_embeddings, metadata)
            logger.info(f"Updated document {doc_id} with {len(new_chunks)} chunks")

        except Exception as e:
            logger.error(f"Error updating document {doc_id}: {str(e)}")
            raise

    def _extract_wiki_links(self, text: str) -> List[Dict[str, str]]:
        """
        Extract Obsidian wiki-style links from text.

        Args:
            text: Text content to extract links from

        Returns:
            List of extracted links with metadata
        """
        import re

        links = []

        # Handle text being a dictionary with content
        if isinstance(text, dict) and "content" in text:
            text = text["content"]

        # Match [[link]] and [[link|alias]] formats
        wiki_pattern = r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]"

        for match in re.finditer(wiki_pattern, text):
            link_target = match.group(1)
            link_alias = match.group(2) if match.group(2) else link_target
            links.append({"target": link_target, "alias": link_alias, "type": "wiki"})

        return links

    def _extract_external_refs(self, text: str) -> List[Dict[str, str]]:
        """
        Extract external references from text.

        Args:
            text: Text content to extract references from

        Returns:
            List of extracted references with metadata
        """
        import re

        refs = []

        # Handle text being a dictionary with content
        if isinstance(text, dict) and "content" in text:
            text = text["content"]

        # Match Markdown links [text](url)
        link_pattern = r"\[([^\]]+)\]\(([^)]+)\)"

        for match in re.finditer(link_pattern, text):
            link_text = match.group(1)
            link_url = match.group(2)
            refs.append({"text": link_text, "url": link_url, "type": "external"})

        return refs

    def _store_link_relationships(
        self, doc_id: str, chunks: List[str], metadata: Dict[str, Any]
    ) -> None:
        """
        Store link relationships between documents.

        Args:
            doc_id: Source document ID
            chunks: List of text chunks
            metadata: Document metadata
        """
        for chunk in chunks:
            # Extract and store wiki links
            wiki_links = self._extract_wiki_links(chunk)
            for link in wiki_links:
                link_id = f"{doc_id}_to_{link['target']}"
                self.collections["links"].upsert(
                    ids=[link_id],
                    embeddings=[
                        [1.0] * self.embedding_dims
                    ],  # Dummy embedding for exact match
                    documents=[""],  # No need to store text
                    metadatas=[
                        {
                            "source_id": doc_id,
                            "target_id": link["target"],
                            "relationship": "references",
                            "link_type": "wiki",
                            "context": chunk[:200],  # Store some context
                        }
                    ],
                )

            # Extract and store external references
            external_refs = self._extract_external_refs(chunk)
            for ref in external_refs:
                ref_id = f"{doc_id}_to_{hash(ref['url'])}"
                self.collections["references"].upsert(
                    ids=[ref_id],
                    embeddings=[
                        [1.0] * self.embedding_dims
                    ],  # Dummy embedding for exact match
                    documents=[ref["url"]],
                    metadatas=[
                        {
                            "source_id": doc_id,
                            "title": ref["text"],
                            "url": ref["url"],
                            "context": chunk[:200],
                        }
                    ],
                )

    def _get_embedding_dimensions(self) -> int:
        """Get the embedding dimensions from the embedding model."""
        if not self.embedding_service:
            raise ValueError("Embedding service is required but not provided")

        # Get a sample embedding to determine dimensions
        sample_text = "Sample text to determine embedding dimensions"
        sample_embedding = self.embedding_service.embed_text(sample_text)
        return len(sample_embedding)
