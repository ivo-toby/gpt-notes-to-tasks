"""
Tests for the LinkService class.

This module contains comprehensive tests for the LinkService functionality,
including relationship analysis, link management, and content suggestions.
"""

import os
import pytest
from unittest.mock import Mock, patch
from services.knowledge.link_service import LinkService

# Test data
SAMPLE_NOTE_CONTENT = """# Test Note

This is a test note with some [[wiki-link]] and a [[another-link|Custom Title]].
It also has [external links](https://example.com).

## Related
- [[related-note]]

---
[[backlink-test]]
"""

@pytest.fixture
def mock_vector_store():
    """Create a mock vector store."""
    mock = Mock()

    # Mock config and path
    mock.config = {
        "path": "~/Documents/notes/.vector_store"
    }

    # Mock find_connected_notes
    mock.find_connected_notes.return_value = [
        {
            "target_id": "wiki-link",
            "relationship": "references",
            "link_type": "wiki",
            "context": "Context for wiki-link"
        }
    ]

    # Mock find_backlinks
    mock.find_backlinks.return_value = [
        {
            "source_id": "source-note",
            "relationship": "references",
            "link_type": "wiki",
            "context": "Context from source note"
        }
    ]

    # Mock get_note_content
    mock.get_note_content.return_value = {
        "content": SAMPLE_NOTE_CONTENT,
        "embedding": [0.1] * 1536,
        "metadata": {"type": "note"}
    }

    # Mock find_similar
    mock.find_similar.return_value = [
        {
            "chunk_id": "similar-note_chunk_1",
            "content": "Similar content",
            "metadata": {"doc_id": "similar-note"},
            "similarity": 0.85
        }
    ]

    # Set chunking_service and embedding_service
    mock.chunking_service = Mock()
    mock.chunking_service.chunk_document.return_value = [
        {
            "content": SAMPLE_NOTE_CONTENT,
            "metadata": {"type": "note"}
        }
    ]

    mock.embedding_service = Mock()
    mock.embedding_service.embed_chunks.return_value = [[0.1] * 1536]

    return mock

@pytest.fixture
def mock_chunking_service():
    """Create a mock chunking service."""
    mock = Mock()
    mock.chunk_document.return_value = [
        {
            "content": SAMPLE_NOTE_CONTENT,
            "metadata": {"type": "note"}
        }
    ]
    return mock

@pytest.fixture
def mock_embedding_service():
    """Create a mock embedding service."""
    mock = Mock()
    mock.embed_chunks.return_value = [[0.1] * 1536]
    return mock

@pytest.fixture
def link_service(mock_vector_store, mock_chunking_service, mock_embedding_service, tmp_path):
    """Create a LinkService instance with mocked dependencies."""
    with patch('services.knowledge.link_service.os.path.exists', return_value=True):
        service = LinkService(mock_vector_store, mock_chunking_service, mock_embedding_service)
        service.base_path = str(tmp_path)
        return service

def test_analyze_relationships(link_service, mock_vector_store):
    """Test relationship analysis for a note."""
    # Set up mock returns
    mock_vector_store.find_connected_notes.return_value = [{"target_id": "wiki-link"}]
    mock_vector_store.find_backlinks.return_value = [{"source_id": "source-note"}]
    mock_vector_store.get_note_content.return_value = {"content": "test content", "embedding": [0.1, 0.2]}
    mock_vector_store.find_similar.return_value = [{"metadata": {"doc_id": "similar-note"}, "content": "similar content", "similarity": 0.8}]

    # Test analysis
    analysis = link_service.analyze_relationships("test-note")

    # Verify direct links were retrieved
    assert len(analysis["direct_links"]) == 1
    assert analysis["direct_links"][0]["target_id"] == "wiki-link"

    # Verify backlinks were retrieved
    assert len(analysis["backlinks"]) == 1
    assert analysis["backlinks"][0]["source_id"] == "source-note"

    # Verify semantic links were found
    assert len(analysis["semantic_links"]) == 1
    assert analysis["semantic_links"][0]["metadata"]["doc_id"] == "similar-note"

    # Verify suggested links were generated
    assert len(analysis["suggested_links"]) > 0

    # Verify vector store calls
    mock_vector_store.find_connected_notes.assert_called_once_with("test-note")
    mock_vector_store.find_backlinks.assert_called_once_with("test-note")

    # Verify find_similar was called twice with different parameters
    assert mock_vector_store.find_similar.call_count == 2
    semantic_call = mock_vector_store.find_similar.call_args_list[0]
    suggestion_call = mock_vector_store.find_similar.call_args_list[1]

    # First call for semantic links
    assert semantic_call.kwargs["limit"] == 5
    assert semantic_call.kwargs["threshold"] == 0.6

    # Second call for suggestions
    assert suggestion_call.kwargs["limit"] == 10
    assert suggestion_call.kwargs["threshold"] == 0.5

def test_update_obsidian_links(link_service, tmp_path):
    """Test updating Obsidian-style wiki links in a note."""
    # Create a test note file
    note_path = tmp_path / "test-note.md"
    with open(note_path, "w") as f:
        f.write(SAMPLE_NOTE_CONTENT)

    # Define links to add
    links_to_add = [
        {
            "add_wiki_link": True,
            "target_id": "new-link",
            "alias": "New Link"
        }
    ]

    # Mock chunking_service to return proper chunks
    link_service.chunking_service.chunk_document.return_value = [
        {
            "content": SAMPLE_NOTE_CONTENT + "\n[[new-link|New Link]]",
            "metadata": {"type": "note"}
        }
    ]

    # Update links
    link_service.update_obsidian_links(str(note_path), links_to_add)

    # Verify the file was updated
    with open(note_path) as f:
        content = f.read()
        assert "[[new-link|New Link]]" in content

def test_generate_alias(link_service):
    """Test alias generation for wiki links."""
    test_cases = [
        ("test-note", "Test Note"),
        ("my_test_note", "My Test Note"),
        ("complex-test-note.md", "Complex Test Note"),
    ]

    for input_id, expected_alias in test_cases:
        alias = link_service._generate_alias(input_id)
        assert alias == expected_alias

def test_has_wiki_link(link_service):
    """Test detection of existing wiki links."""
    content = SAMPLE_NOTE_CONTENT

    # Test existing links
    assert link_service._has_wiki_link(content, "wiki-link")
    assert link_service._has_wiki_link(content, "another-link")
    assert link_service._has_wiki_link(content, "backlink-test")

    # Test non-existent links
    assert not link_service._has_wiki_link(content, "nonexistent-link")

def test_insert_wiki_link(link_service):
    """Test insertion of new wiki links."""
    # Test insertion with existing separator
    content = "Test content\n\n---\nExisting links"
    new_link = "[[new-link]]"
    result = link_service._insert_wiki_link(content, new_link)
    assert "---\nExisting links\n[[new-link]]" in result

    # Test insertion without existing separator
    content = "Test content"
    result = link_service._insert_wiki_link(content, new_link)
    assert "Test content\n\n---\n[[new-link]]" in result

def test_update_target_backlinks(link_service, tmp_path):
    """Test updating backlinks in target notes."""
    # Create a target note file
    target_path = tmp_path / "target-note.md"
    with open(target_path, "w") as f:
        f.write("# Target Note\n\nSome content")

    # Mock chunking_service to return proper chunks
    link_service.chunking_service.chunk_document.return_value = [
        {
            "content": "# Target Note\n\nSome content",
            "metadata": {"type": "note"}
        }
    ]

    # Mock vector_store methods
    link_service.vector_store.get_note_content.return_value = {
        "content": "# Target Note\n\nSome content",
        "embedding": [0.1, 0.2]
    }

    # Update backlinks
    link_service._update_target_backlinks(
        "target-note",
        "source-note",
        str(target_path)
    )

    # Verify the file was updated with backlinks section
    with open(target_path) as f:
        content = f.read()
        assert "# Target Note" in content
        assert "Some content" in content
        assert "[[source-note]]" in content

def test_error_handling(link_service):
    """Test error handling in various scenarios."""
    # Mock os.path.exists to return False for the nonexistent file
    with patch('services.knowledge.link_service.os.path.exists', return_value=False):
        # Test with non-existent note by trying to update links
        with pytest.raises(FileNotFoundError):
            link_service.update_obsidian_links(
                "nonexistent.md",
                [{"target_id": "test", "add_wiki_link": True}]
            )

if __name__ == "__main__":
    pytest.main([__file__])