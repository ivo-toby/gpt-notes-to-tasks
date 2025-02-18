"""
Tests for the EmbeddingService class.

This module contains comprehensive tests for the EmbeddingService functionality,
including model initialization, embedding generation, and error handling.
"""

import pytest
from unittest.mock import Mock, patch
from services.vector_store.embedding_service import EmbeddingService

# Constants for test dimensions
OPENAI_DIMENSION = 1536
OLLAMA_DIMENSION = 1024  # Default dimension for Ollama models

@pytest.fixture
def mock_openai_embeddings():
    """Mock OpenAI embeddings model."""
    mock_instance = Mock()
    mock_instance.embed_query.return_value = [0.1] * OPENAI_DIMENSION
    mock_instance.embed_documents.return_value = [[0.1] * OPENAI_DIMENSION for _ in range(3)]
    return mock_instance

@pytest.fixture
def mock_ollama_embeddings():
    """Mock Ollama embeddings model."""
    mock_instance = Mock()
    mock_instance.embed_query.return_value = [0.1] * OLLAMA_DIMENSION
    mock_instance.embed_documents.return_value = [[0.1] * OLLAMA_DIMENSION for _ in range(3)]
    return mock_instance

@pytest.fixture
def openai_config(sample_config):
    """Sample configuration for OpenAI embeddings."""
    config = sample_config.copy()
    config["api_key"] = "test-api-key"  # Add API key for OpenAI tests
    config["embeddings"] = {
        "model_type": "openai",
        "model_name": "text-embedding-3-small",
        "batch_size": 100,
        "model_kwargs": {
            "device": "cpu",
            "normalize_embeddings": True
        }
    }
    return config

@pytest.fixture
def ollama_config(sample_config):
    """Sample configuration for Ollama embeddings."""
    config = sample_config.copy()
    config["embeddings"] = {
        "model_type": "ollama",
        "model_name": "mxbai-embed-large:latest",
        "batch_size": 100,
        "ollama_config": {
            "base_url": "http://localhost:11434",
            "num_ctx": 512,
            "num_thread": 4
        }
    }
    return config

def test_init_openai_embeddings(openai_config, mock_openai_embeddings):
    """Test initialization with OpenAI embeddings."""
    with patch("services.vector_store.embedding_service.OpenAIEmbeddings", return_value=mock_openai_embeddings):
        service = EmbeddingService(openai_config)
        assert service.model_type == "openai"
        assert service.model_name == "text-embedding-3-small"
        assert service.batch_size == 100
        assert service.model == mock_openai_embeddings

def test_init_ollama_embeddings(ollama_config, mock_ollama_embeddings):
    """Test initialization with Ollama embeddings."""
    with patch("services.vector_store.embedding_service.OllamaEmbeddings", return_value=mock_ollama_embeddings):
        service = EmbeddingService(ollama_config)
        assert service.model_type == "ollama"
        assert service.model_name == "mxbai-embed-large:latest"
        assert service.batch_size == 100
        assert service.model == mock_ollama_embeddings

def test_init_invalid_model_type(sample_config):
    """Test initialization with invalid model type."""
    config = sample_config.copy()
    config["embeddings"] = {"model_type": "invalid"}
    with pytest.raises(ValueError, match="Unsupported embedding model type"):
        EmbeddingService(config)

@pytest.mark.parametrize("model_type,dimension", [
    ("openai", OPENAI_DIMENSION),
    ("ollama", OLLAMA_DIMENSION)
])
def test_embed_text(sample_config, model_type, dimension):
    """Test single text embedding generation."""
    config = sample_config.copy()
    if model_type == "openai":
        config["api_key"] = "test-api-key"
    config["embeddings"]["model_type"] = model_type

    mock_instance = Mock()
    mock_instance.embed_query.return_value = [0.1] * dimension

    if model_type == "openai":
        patch_path = "services.vector_store.embedding_service.OpenAIEmbeddings"
    else:
        patch_path = "services.vector_store.embedding_service.OllamaEmbeddings"

    with patch(patch_path, return_value=mock_instance):
        service = EmbeddingService(config)
        embedding = service.embed_text("test text")

        assert len(embedding) == dimension
        mock_instance.embed_query.assert_called_once_with("test text")

def test_embed_chunks_openai(openai_config, mock_openai_embeddings):
    """Test batch embedding generation with OpenAI."""
    with patch("services.vector_store.embedding_service.OpenAIEmbeddings", return_value=mock_openai_embeddings):
        service = EmbeddingService(openai_config)
        chunks = ["text1", "text2", "text3"]

        embeddings = service.embed_chunks(chunks)

        assert len(embeddings) == len(chunks)
        assert all(len(emb) == OPENAI_DIMENSION for emb in embeddings)
        mock_openai_embeddings.embed_documents.assert_called_once_with(chunks)

def test_embed_chunks_ollama(ollama_config, mock_ollama_embeddings):
    """Test batch embedding generation with Ollama."""
    with patch("services.vector_store.embedding_service.OllamaEmbeddings", return_value=mock_ollama_embeddings):
        service = EmbeddingService(ollama_config)
        chunks = ["text1", "text2", "text3"]

        embeddings = service.embed_chunks(chunks)

        assert len(embeddings) == len(chunks)
        assert all(len(emb) == OLLAMA_DIMENSION for emb in embeddings)
        mock_ollama_embeddings.embed_documents.assert_called_once_with(chunks)

def test_embed_chunks_batching(openai_config, mock_openai_embeddings):
    """Test batch processing with size limits."""
    with patch("services.vector_store.embedding_service.OpenAIEmbeddings", return_value=mock_openai_embeddings):
        openai_config["embeddings"]["batch_size"] = 2
        service = EmbeddingService(openai_config)
        chunks = ["text1", "text2", "text3", "text4", "text5"]

        # Configure mock to return one embedding per input chunk for each batch
        def mock_embed_documents(batch):
            return [[0.1] * OPENAI_DIMENSION for _ in range(len(batch))]
        mock_openai_embeddings.embed_documents.side_effect = mock_embed_documents

        embeddings = service.embed_chunks(chunks)

        assert len(embeddings) == len(chunks)
        assert all(len(emb) == OPENAI_DIMENSION for emb in embeddings)
        # Should have been called 3 times: [text1,text2], [text3,text4], [text5]
        assert mock_openai_embeddings.embed_documents.call_count == 3

def test_get_embedding_metadata_openai(openai_config, mock_openai_embeddings):
    """Test metadata retrieval for OpenAI embeddings."""
    with patch("services.vector_store.embedding_service.OpenAIEmbeddings", return_value=mock_openai_embeddings):
        service = EmbeddingService(openai_config)
        metadata = service.get_embedding_metadata()

        assert metadata["model_type"] == "openai"
        assert metadata["model_name"] == "text-embedding-3-small"
        assert metadata["dimensions"] == OPENAI_DIMENSION
        assert metadata["normalized"] is True
        assert metadata["batch_size"] == 100

def test_get_embedding_metadata_ollama(ollama_config, mock_ollama_embeddings):
    """Test metadata retrieval for Ollama embeddings."""
    with patch("services.vector_store.embedding_service.OllamaEmbeddings", return_value=mock_ollama_embeddings):
        service = EmbeddingService(ollama_config)
        metadata = service.get_embedding_metadata()

        assert metadata["model_type"] == "ollama"
        assert metadata["model_name"] == "mxbai-embed-large:latest"
        assert metadata["dimensions"] == OLLAMA_DIMENSION
        assert metadata["normalized"] is True
        assert metadata["batch_size"] == 100
        assert metadata["ollama_base_url"] == "http://localhost:11434"
        assert metadata["ollama_num_ctx"] == 512
        assert metadata["ollama_num_thread"] == 4

@pytest.mark.parametrize("error_type", [
    ConnectionError,
    TimeoutError,
    ValueError
])
def test_embed_text_error_handling(openai_config, mock_openai_embeddings, error_type):
    """Test error handling during embedding generation."""
    with patch("services.vector_store.embedding_service.OpenAIEmbeddings", return_value=mock_openai_embeddings):
        service = EmbeddingService(openai_config)
        mock_openai_embeddings.embed_query.side_effect = error_type("Test error")

        with pytest.raises(Exception):
            service.embed_text("test text")

if __name__ == "__main__":
    pytest.main([__file__])