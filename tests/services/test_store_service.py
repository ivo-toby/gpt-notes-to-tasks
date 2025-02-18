"""
Tests for the VectorStoreService class.

This module contains comprehensive tests for the VectorStoreService functionality,
including document storage, retrieval, and relationship management.
"""

import json
import os
import time
from unittest.mock import Mock, patch
import pytest
from chromadb.api.models.Collection import Collection
from services.vector_store.store_service import VectorStoreService
import chromadb
from chromadb.config import Settings
from sqlite3 import OperationalError

# Test data
SAMPLE_DOCUMENT = {
    "id": "test-note",
    "content": "This is a test note with [[wiki-link]] and [external link](https://example.com)",
    "type": "note",
    "modified_time": time.time(),
}

SAMPLE_CHUNKS = [
    "This is a test note with [[wiki-link]]",
    "and [external link](https://example.com)"
]

SAMPLE_EMBEDDINGS = [
    [0.1] * 1536,  # OpenAI dimension
    [0.2] * 1536
]

@pytest.fixture
def mock_chromadb_client():
    """Create a mock ChromaDB client."""
    client = Mock()

    # Create mock collections
    notes_collection = Mock(spec=Collection)
    links_collection = Mock(spec=Collection)
    metadata_collection = Mock(spec=Collection)
    system_collection = Mock(spec=Collection)
    references_collection = Mock(spec=Collection)

    # Setup collection returns
    def get_or_create_collection(name, **kwargs):
        collections = {
            "notes": notes_collection,
            "links": links_collection,
            "metadata": metadata_collection,
            "system": system_collection,
            "references": references_collection
        }
        return collections[name]

    client.get_or_create_collection = Mock(side_effect=get_or_create_collection)

    return client

@pytest.fixture
def mock_chunking_service():
    """Create a mock chunking service."""
    mock = Mock()
    mock.chunk_document.return_value = SAMPLE_CHUNKS
    return mock

@pytest.fixture
def mock_embedding_service():
    """Create a mock embedding service."""
    mock = Mock()
    mock.embed_chunks.return_value = SAMPLE_EMBEDDINGS
    return mock

@pytest.fixture
def store_config():
    """Create test configuration."""
    return {
        "vector_store": {
            "path": "/tmp/test_vector_store",
            "distance_func": "cosine",
            "hnsw_space": "cosine",
            "hnsw_config": {
                "ef_construction": 400,
                "ef_search": 200,
                "m": 128
            }
        }
    }

@pytest.fixture
def mock_settings():
    """Mock ChromaDB settings."""
    settings = Mock(spec=Settings)
    settings.persist_directory = "/tmp/test_vector_store"
    settings.allow_reset = True
    settings.anonymized_telemetry = False
    return settings

@pytest.fixture
def vector_store(mock_chromadb_client, store_config):
    """Create a VectorStoreService instance with mocked dependencies."""
    with patch('chromadb.PersistentClient', return_value=mock_chromadb_client), \
         patch('os.path.expanduser', side_effect=lambda x: x), \
         patch('os.makedirs', return_value=None):
        service = VectorStoreService(store_config)

        # Setup default return values for collections
        service.collections["notes"].query.return_value = {
            "ids": [["test-note_chunk_0"]],
            "documents": [["Test content"]],
            "metadatas": [[{"doc_id": "test-note", "chunk_index": 0, "doc_type": "note"}]],
            "embeddings": [[[0.1] * 1536]]
        }

        service.metadata_collection.get.return_value = {
            "ids": ["test-note"],
            "metadatas": [{"modified_time": 123456789}]
        }

        service.collections["links"].query.return_value = {
            "ids": ["link-1"],
            "documents": [["Connected note"]],
            "metadatas": [{"source_id": "test-note", "target_id": "connected-note"}],
            "distances": [0.1]
        }

        return service

def test_initialization(vector_store, store_config):
    """Test initialization of collections and parameters."""
    # Verify collections were created
    assert vector_store.collections["notes"] is not None
    assert vector_store.collections["links"] is not None
    assert vector_store.metadata_collection is not None
    assert vector_store.system_collection is not None

    # Verify configuration
    assert vector_store.db_path == store_config["vector_store"]["path"]

def test_add_document(vector_store):
    """Test adding a new document."""
    # Patch the extract methods to handle content directly
    with patch.object(vector_store, '_extract_wiki_links') as mock_wiki_links, \
         patch.object(vector_store, '_extract_external_refs') as mock_external_refs:
        mock_wiki_links.return_value = []
        mock_external_refs.return_value = []

        # Add document
        vector_store.add_document(
            doc_id="test-note",
            chunks=SAMPLE_CHUNKS,
            embeddings=SAMPLE_EMBEDDINGS
        )

        # Verify notes collection was updated
        notes_collection = vector_store.collections["notes"]
        notes_collection.upsert.assert_called_once_with(
            ids=["test-note_chunk_0", "test-note_chunk_1"],
            documents=SAMPLE_CHUNKS,
            embeddings=SAMPLE_EMBEDDINGS,
            metadatas=[{
                "doc_id": "test-note",
                "chunk_index": idx,
                "doc_type": "note",
                "source_path": "",
                "date": "",
                "filename": ""
            } for idx in range(len(SAMPLE_CHUNKS))]
        )

def test_find_connected_notes(vector_store):
    """Test finding connected notes."""
    # Mock links collection to return some connections
    links_collection = vector_store.collections["links"]
    links_collection.query.return_value = {
        "ids": ["connection1"],
        "metadatas": [[{  # Note the double list
            "target_id": "connected-note",
            "relationship": "references",
            "link_type": "wiki"
        }]]
    }

    results = vector_store.find_connected_notes("test-note")

    # Verify query was executed
    links_collection.query.assert_called_once()

    # Verify results
    assert len(results) == 1
    assert results[0]["target_id"] == "connected-note"
    assert results[0]["relationship"] == "references"
    assert results[0]["link_type"] == "wiki"

def test_find_backlinks(vector_store):
    """Test finding backlinks."""
    # Mock links collection to return some backlinks
    links_collection = vector_store.collections["links"]
    links_collection.query.return_value = {
        "ids": ["backlink1"],
        "metadatas": [[{  # Note the double list
            "source_id": "source-note",
            "relationship": "references",
            "link_type": "wiki"
        }]]
    }

    results = vector_store.find_backlinks("test-note")

    # Verify query was executed
    links_collection.query.assert_called_once()

    # Verify results
    assert len(results) == 1
    assert results[0]["source_id"] == "source-note"
    assert results[0]["relationship"] == "references"
    assert results[0]["link_type"] == "wiki"

def test_get_note_content(vector_store):
    """Test retrieving note content."""
    result = vector_store.get_note_content("test-note")

    # Verify query was executed with correct parameters
    notes_collection = vector_store.collections["notes"]
    notes_collection.query.assert_called_once_with(
        query_embeddings=[[1.0] * 1536],
        where={"doc_id": "test-note"},
        include=["documents", "metadatas", "embeddings"]
    )

    # Verify result format
    assert result == {
        "content": "Test content",
        "metadata": {"doc_id": "test-note", "chunk_index": 0, "doc_type": "note"},
        "embedding": [0.1] * 1536
    }

def test_update_document(vector_store):
    """Test updating an existing document."""
    new_chunks = ["Updated content"]
    new_embeddings = [[0.3] * 1536]

    vector_store.update_document(
        doc_id="test-note",
        new_chunks=new_chunks,
        new_embeddings=new_embeddings
    )

    # Verify old content was deleted
    notes_collection = vector_store.collections["notes"]
    notes_collection.delete.assert_called_once_with(where={"doc_id": "test-note"})

    # Verify links were deleted
    links_collection = vector_store.collections["links"]
    links_collection.delete.assert_called_once_with(where={"source_id": "test-note"})

    # Verify new content was added
    notes_collection.upsert.assert_called_once_with(
        ids=["test-note_chunk_0"],
        documents=new_chunks,
        embeddings=new_embeddings,
        metadatas=[{
            "doc_id": "test-note",
            "chunk_index": 0,
            "doc_type": "note",
            "source_path": "",
            "date": "",
            "filename": ""
        }]
    )

def test_needs_update(vector_store):
    """Test checking if a document needs updating."""
    # Test when document exists
    result = vector_store.needs_update("test-note", 123456790)
    assert result is True

    # Test when document doesn't exist
    vector_store.metadata_collection.get.return_value = {"ids": [], "metadatas": []}
    result = vector_store.needs_update("test-note", 123456789)
    assert result is True

def test_last_update_time(vector_store):
    """Test getting and setting last update time."""
    # Test getting last update time
    vector_store.system_collection.get.return_value = {
        "ids": ["last_update"],
        "metadatas": [{"timestamp": "123456789"}]
    }
    last_time = vector_store.get_last_update_time()
    assert last_time == 123456789

    # Test setting last update time
    new_time = 123456790
    vector_store.set_last_update_time(new_time)
    vector_store.system_collection.upsert.assert_called_once_with(
        ids=["last_update"],
        metadatas=[{"timestamp": str(new_time)}],
        embeddings=[[1.0] * 1536],
        documents=[""]
    )

def test_retry_operation(vector_store):
    """Test retry mechanism for database operations."""
    operation = Mock(side_effect=[OperationalError("DB locked"), OperationalError("DB locked"), "success"])
    result = vector_store._retry_operation(operation)
    assert result == "success"
    assert operation.call_count == 3

def test_error_handling(vector_store):
    """Test error handling for various operations."""
    # Test error handling for get_note_content
    vector_store.collections["notes"].query.side_effect = Exception("Database error")
    result = vector_store.get_note_content("test-note")
    assert result is None

    # Test error handling for update_document
    vector_store.collections["notes"].delete.side_effect = Exception("Database error")
    with pytest.raises(Exception):
        vector_store.update_document(
            doc_id="test-note",
            new_chunks=["content"],
            new_embeddings=[[0.1] * 1536]
        )

if __name__ == "__main__":
    pytest.main([__file__])