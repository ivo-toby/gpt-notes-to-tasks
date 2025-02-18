"""
Tests for the ChunkingService class.

This module contains comprehensive tests for the ChunkingService functionality,
including document chunking, metadata extraction, and configuration handling.
"""

import pytest
from services.vector_store.chunking_service import ChunkingService

# Test data
SAMPLE_MARKDOWN = """# Test Document

## Section 1
This is a test paragraph with some content.
It spans multiple lines and includes some #tags.

## Section 2
Another paragraph with different content.
This one has a [[wiki-link]] and a [regular link](https://example.com).

## Section 3
Final section with some code:
```python
def test():
    print("Hello")
```

#test #documentation
"""

SAMPLE_CODE = """
def example_function():
    \"\"\"
    This is a docstring explaining the function.
    It has multiple lines of documentation.
    \"\"\"
    # This is a comment
    print("Hello, World!")  # Inline comment

    # Another comment block
    for i in range(10):
        if i % 2 == 0:
            print(f"Even number: {i}")
"""

@pytest.fixture
def chunking_config(sample_config):
    """Sample configuration for chunking service."""
    config = sample_config.copy()
    config["chunking_config"] = {
        "recursive": {
            "chunk_size": 500,
            "chunk_overlap": 50
        }
    }
    return config

@pytest.fixture
def chunking_service(chunking_config):
    """Create a ChunkingService instance with test configuration."""
    return ChunkingService(chunking_config)

def test_chunk_document_markdown(chunking_service):
    """Test chunking a markdown document."""
    chunks = chunking_service.chunk_document(SAMPLE_MARKDOWN, doc_type="note")

    assert len(chunks) > 0
    for chunk in chunks:
        assert isinstance(chunk, dict)
        assert "content" in chunk
        assert "metadata" in chunk
        assert len(chunk["content"]) <= chunking_service.chunk_size

def test_chunk_document_code(chunking_service):
    """Test chunking a code document."""
    chunks = chunking_service.chunk_document(SAMPLE_CODE, doc_type="code")

    assert len(chunks) > 0
    for chunk in chunks:
        assert isinstance(chunk, dict)
        assert "content" in chunk
        assert "metadata" in chunk
        assert chunk["metadata"]["doc_type"] == "code"

def test_metadata_extraction(chunking_service):
    """Test metadata extraction from chunks."""
    # Extract tags from the content
    tags = ["#test", "#documentation"]
    chunks = chunking_service.chunk_document(SAMPLE_MARKDOWN, doc_type="note", tags=tags)

    for chunk in chunks:
        metadata = chunk["metadata"]
        assert "doc_type" in metadata
        assert "char_count" in metadata
        assert isinstance(metadata["char_count"], int)
        assert "tags" in metadata
        assert metadata["tags"] == tags

def test_chunk_size_limits(chunking_service):
    """Test that chunks respect size limits."""
    # Create a long document
    long_text = "word " * 1000
    chunks = chunking_service.chunk_document(long_text, doc_type="note")

    for chunk in chunks:
        assert len(chunk["content"]) <= chunking_service.chunk_size

def test_chunk_overlap(chunking_service):
    """Test chunk overlap functionality."""
    # Create text with distinct sections
    text = "Section1 " * 50 + "Overlap " * 10 + "Section2 " * 50
    chunks = chunking_service.chunk_document(text, doc_type="note")

    if len(chunks) > 1:
        # Check if overlap text appears in consecutive chunks
        for i in range(len(chunks) - 1):
            overlap_size = chunking_service.chunk_overlap
            assert any(
                word in chunks[i+1]["content"]
                for word in chunks[i]["content"][-overlap_size:].split()
            )

def test_empty_document(chunking_service):
    """Test handling of empty documents."""
    chunks = chunking_service.chunk_document("", doc_type="note")
    assert len(chunks) == 0

def test_small_document(chunking_service):
    """Test handling of documents smaller than chunk size."""
    small_text = "This is a small document."
    chunks = chunking_service.chunk_document(small_text, doc_type="note")
    assert len(chunks) == 1
    assert chunks[0]["content"] == small_text

@pytest.mark.parametrize("doc_type", ["note", "code", "meeting", "learning"])
def test_different_document_types(chunking_service, doc_type):
    """Test chunking with different document types."""
    text = f"This is a test {doc_type} document."
    chunks = chunking_service.chunk_document(text, doc_type=doc_type)
    assert chunks[0]["metadata"]["doc_type"] == doc_type

def test_custom_chunk_size(chunking_config):
    """Test chunking with custom chunk size."""
    chunking_config["chunking_config"]["recursive"]["chunk_size"] = 100
    service = ChunkingService(chunking_config)

    text = "word " * 50
    chunks = service.chunk_document(text, doc_type="note")

    for chunk in chunks:
        assert len(chunk["content"]) <= service.chunk_size

def test_markdown_structure_preservation(chunking_service):
    """Test that markdown structure is preserved in chunks."""
    markdown = """
# Header

## Subheader
Content under subheader.

### Sub-subheader
More content here.
"""
    chunks = chunking_service.chunk_document(markdown, doc_type="note")

    # Check that headers are preserved at chunk boundaries
    for chunk in chunks:
        # Headers should start with #
        if chunk["content"].strip().startswith("#"):
            assert any(line.startswith("#") for line in chunk["content"].split("\n"))

def test_code_block_handling(chunking_service):
    """Test handling of code blocks in markdown."""
    markdown = """
Here's some code:
```python
def test():
    print("Hello")
```
And more text.
"""
    chunks = chunking_service.chunk_document(markdown, doc_type="note")

    # Find chunk containing code block
    code_chunk = next((chunk for chunk in chunks
                      if "```python" in chunk["content"]), None)
    if code_chunk:
        # Code block should be complete
        assert "```python" in code_chunk["content"]
        assert "```" in code_chunk["content"].split("```python")[1]

if __name__ == "__main__":
    pytest.main([__file__])