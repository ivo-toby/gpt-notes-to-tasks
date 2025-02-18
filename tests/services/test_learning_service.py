"""
Tests for the learning service.

This module contains tests for the learning service functionality,
including loading, identifying, and processing learning entries.
"""

import os
from unittest.mock import Mock, patch
import pytest
from pathlib import Path

from services.learning_service import LearningService
from services.openai_service import OpenAIService


@pytest.fixture
def sample_learning_content():
    """Return sample learning content for testing."""
    return """
[2024-02-18 10:30:00 AM] Learning about pytest fixtures
Really interesting how fixtures can be scoped and shared.

[2024-02-18 11:45:00 AM] Git branching strategies
Understanding the differences between Git Flow and trunk-based development.
"""


@pytest.fixture
def learning_service(temp_dir):
    """Create a LearningService instance with temporary directories."""
    learnings_file = temp_dir / "learnings.md"
    learnings_output_dir = temp_dir / "processed"
    return LearningService(str(learnings_file), str(learnings_output_dir))


def test_load_learnings(learning_service, sample_learning_content, temp_dir):
    """Test loading learning entries from a file."""
    # Setup
    learnings_file = Path(learning_service.learnings_file)
    learnings_file.write_text(sample_learning_content)

    # Execute
    content = learning_service.load_learnings()

    # Assert
    assert content == sample_learning_content


def test_identify_new_learnings(learning_service, sample_learning_content):
    """Test extracting learning entries from content."""
    # Execute
    learnings = learning_service.identify_new_learnings(sample_learning_content)

    # Assert
    assert len(learnings) == 2

    # Check first learning
    assert learnings[0][1] == "2024-02-18 10:30:00 AM"
    assert "pytest fixtures" in learnings[0][2]

    # Check second learning
    assert learnings[1][1] == "2024-02-18 11:45:00 AM"
    assert "Git branching" in learnings[1][2]


def test_generate_markdown_file(learning_service):
    """Test generating a markdown file for a learning entry."""
    # Setup
    timestamp = "2024-02-18 10:30:00 AM"
    learning = "Understanding how to write effective tests"
    title = "Test Writing Best Practices"
    tags = ["testing", "pytest", "best-practices"]

    # Execute
    filename = learning_service.generate_markdown_file(timestamp, learning, title, tags)

    # Assert
    expected_path = Path(learning_service.learnings_output_dir) / filename
    assert expected_path.exists()

    content = expected_path.read_text()
    assert title in content
    assert timestamp in content
    assert learning in content
    assert all(tag in content for tag in tags)


def test_process_new_learnings(learning_service, sample_learning_content):
    """Test processing new learning entries with mocked OpenAI service."""
    # Setup
    learnings_file = Path(learning_service.learnings_file)
    learnings_file.write_text(sample_learning_content)

    mock_openai = Mock(spec=OpenAIService)
    mock_openai.generate_learning_title.return_value = "Sample Learning Title"
    mock_openai.generate_learning_tags.return_value = ["tag1", "tag2"]

    # Execute
    learning_service.process_new_learnings(mock_openai)

    # Assert
    # Check that files were created
    output_dir = Path(learning_service.learnings_output_dir)
    assert output_dir.exists()
    assert len(list(output_dir.glob("*.md"))) == 2

    # Verify OpenAI service was called for each learning
    assert mock_openai.generate_learning_title.call_count == 2
    assert mock_openai.generate_learning_tags.call_count == 2

    # Check that original file was updated
    assert learnings_file.read_text().strip() == ""


def test_process_new_learnings_creates_output_dir(learning_service, sample_learning_content):
    """Test that processing creates the output directory if it doesn't exist."""
    # Setup
    learnings_file = Path(learning_service.learnings_file)
    learnings_file.write_text(sample_learning_content)

    output_dir = Path(learning_service.learnings_output_dir)
    if output_dir.exists():
        output_dir.rmdir()

    mock_openai = Mock(spec=OpenAIService)
    mock_openai.generate_learning_title.return_value = "Sample Title"
    mock_openai.generate_learning_tags.return_value = ["tag1"]

    # Execute
    learning_service.process_new_learnings(mock_openai)

    # Assert
    assert output_dir.exists()
    assert len(list(output_dir.glob("*.md"))) == 2