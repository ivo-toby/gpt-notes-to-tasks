"""
Tests for file handling utilities.

This module contains tests for file-related utility functions.
"""

import os
from pathlib import Path
from unittest.mock import patch, mock_open, Mock

import pytest

from utils.file_handler import load_notes, write_summary_to_file, create_output_dir


@pytest.fixture
def sample_notes():
    """Return sample notes content for testing."""
    return """
[2024-02-18 10:30:00 AM] First note entry
Some content here.

[2024-02-18 11:45:00 AM] Second note entry
More content here.
"""


def test_load_notes_success(temp_dir, sample_notes):
    """Test successful loading of notes from a file."""
    # Setup
    notes_file = temp_dir / "notes.md"
    notes_file.write_text(sample_notes)

    # Execute
    content = load_notes(str(notes_file))

    # Assert
    assert content == sample_notes


def test_load_notes_file_not_found():
    """Test loading notes when file doesn't exist."""
    # Setup
    non_existent_file = "/path/to/nonexistent/file.md"

    # Execute
    content = load_notes(non_existent_file)

    # Assert
    assert content == ""


def test_load_notes_expands_home():
    """Test that load_notes expands home directory."""
    # Setup
    with patch("os.path.expanduser") as mock_expanduser, \
         patch("builtins.open", mock_open(read_data="test content")):
        mock_expanduser.return_value = "/home/user/notes.md"

        # Execute
        content = load_notes("~/notes.md")

        # Assert
        mock_expanduser.assert_called_once_with("~/notes.md")
        assert content == "test content"


def test_write_summary_to_file(temp_dir):
    """Test writing summary content to a file."""
    # Setup
    output_file = temp_dir / "summary.md"
    content = "Test summary content"

    # Execute
    write_summary_to_file(str(output_file), content)

    # Assert
    assert output_file.exists()
    assert output_file.read_text() == content


def test_write_summary_to_file_creates_parent_dirs(temp_dir):
    """Test that write_summary_to_file creates parent directories."""
    # Setup
    output_file = temp_dir / "subdir" / "nested" / "summary.md"
    content = "Test summary content"

    # Execute
    write_summary_to_file(str(output_file), content)

    # Assert
    assert output_file.exists()
    assert output_file.read_text() == content
    assert output_file.parent.is_dir()


def test_write_summary_to_file_expands_home():
    """Test that write_summary_to_file expands home directory."""
    # Setup
    with patch("os.path.expanduser") as mock_expanduser, \
         patch("os.path.dirname") as mock_dirname, \
         patch("os.mkdir") as mock_mkdir, \
         patch("utils.file_handler.Path") as mock_path_class, \
         patch("builtins.open", mock_open()) as mock_file:
        mock_expanduser.return_value = "/home/user/summary.md"
        mock_dirname.return_value = "/home/user"
        mock_path_instance = Mock()
        mock_path_class.return_value = mock_path_instance

        # Execute
        write_summary_to_file("~/summary.md", "test content")

        # Assert
        mock_expanduser.assert_called_once_with("~/summary.md")
        mock_dirname.assert_called_once_with("/home/user/summary.md")
        mock_path_class.assert_called_once_with("/home/user")
        mock_path_instance.mkdir.assert_called_once_with(parents=True, exist_ok=True)
        mock_file.assert_called_once_with("/home/user/summary.md", "w", encoding="utf-8")


def test_create_output_dir(temp_dir):
    """Test creating output directory."""
    # Setup
    output_dir = temp_dir / "output"

    # Execute
    result = create_output_dir(str(output_dir))

    # Assert
    assert Path(result).exists()
    assert Path(result).is_dir()


def test_create_output_dir_existing(temp_dir):
    """Test creating output directory when it already exists."""
    # Setup
    output_dir = temp_dir / "output"
    output_dir.mkdir()

    # Execute
    result = create_output_dir(str(output_dir))

    # Assert
    assert Path(result).exists()
    assert Path(result).is_dir()


def test_create_output_dir_expands_home():
    """Test that create_output_dir expands home directory."""
    # Setup
    with patch("os.path.expanduser") as mock_expanduser, \
         patch("os.mkdir") as mock_mkdir, \
         patch("utils.file_handler.Path") as mock_path_class:
        mock_expanduser.return_value = "/home/user/output"
        mock_path_instance = Mock()
        mock_path_class.return_value = mock_path_instance

        # Execute
        result = create_output_dir("~/output")

        # Assert
        mock_expanduser.assert_called_once_with("~/output")
        mock_path_class.assert_called_once_with("/home/user/output")
        mock_path_instance.mkdir.assert_called_once_with(parents=True, exist_ok=True)
        assert result == "/home/user/output"