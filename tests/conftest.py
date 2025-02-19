"""
Common test configurations and fixtures.

This module contains pytest configurations and fixtures that can be
shared across multiple test files.
"""

import pytest
import os
import tempfile
from pathlib import Path

@pytest.fixture(scope="session")
def test_data_dir():
    """Create a temporary directory for test data that persists across the test session."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)

@pytest.fixture(scope="session")
def sample_config():
    """Return a sample configuration dictionary for testing."""
    return {
        "notes_base_dir": "~/Documents/notes",
        "daily_notes_file": "~/Documents/notes/daily/daily.md",
        "daily_output_dir": "~/Documents/notes/daily",
        "weekly_output_dir": "~/Documents/notes/weekly",
        "meeting_notes_output_dir": "~/Documents/notes/meetingnotes",
        "learnings_file": "~/Documents/notes/learnings/learnings.md",
        "learnings_output_dir": "~/Documents/notes/learnings",
        "vector_store": {
            "path": "~/Documents/notes/.vector_store",
            "chunk_size_min": 50,
            "chunk_size_max": 500,
            "similarity_threshold": -250.0
        },
        "embeddings": {
            "model_type": "ollama",
            "model_name": "mxbai-embed-large:latest",
            "batch_size": 100,
            "ollama_config": {
                "base_url": "http://localhost:11434",
                "num_ctx": 512,
                "num_thread": 4
            }
        }
    }

@pytest.fixture
def temp_file():
    """Create a temporary file that is removed after the test."""
    fd, path = tempfile.mkstemp()
    yield path
    os.close(fd)
    if os.path.exists(path):
        os.unlink(path)

@pytest.fixture
def temp_dir():
    """Create a temporary directory that is removed after the test."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)