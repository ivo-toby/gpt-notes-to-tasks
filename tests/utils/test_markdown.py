"""
Tests for markdown utilities.

This module contains tests for markdown-related utility functions.
"""

import pytest

from utils.markdown import create_daily_summary_content, create_weekly_summary_content


def test_create_daily_summary_content():
    """Test creating daily summary content."""
    # Setup
    summary = "Test summary"
    tasks = ["Task 1", "Task 2"]
    tags = ["tag1", "tag2"]
    notes = "Original notes content"

    # Execute
    content = create_daily_summary_content(summary, tasks, tags, notes)

    # Assert
    assert "# Daily Summary" in content
    assert "## Summary" in content
    assert summary in content
    assert "## Action Items" in content
    for task in tasks:
        assert f"- {task}" in content
    assert "### Tags" in content
    for tag in tags:
        assert f"#{tag}" in content
    assert "## Original Notes" in content
    assert notes in content


def test_create_daily_summary_content_empty_lists():
    """Test creating daily summary content with empty lists."""
    # Setup
    summary = "Test summary"
    tasks = []
    tags = []
    notes = "Original notes content"

    # Execute
    content = create_daily_summary_content(summary, tasks, tags, notes)

    # Assert
    assert "# Daily Summary" in content
    assert "## Summary" in content
    assert summary in content
    assert "## Action Items" in content
    assert "### Tags" in content
    assert "## Original Notes" in content
    assert notes in content


def test_create_weekly_summary_content():
    """Test creating weekly summary content."""
    # Setup
    summary = "Test weekly summary"
    notes = "Original weekly notes"

    # Execute
    content = create_weekly_summary_content(summary, notes)

    # Assert
    assert "# Weekly Summary" in content
    assert "## Summary" in content
    assert summary in content
    assert "## Original Notes" in content
    assert notes in content


def test_create_weekly_summary_content_empty_notes():
    """Test creating weekly summary content with empty notes."""
    # Setup
    summary = "Test weekly summary"
    notes = ""

    # Execute
    content = create_weekly_summary_content(summary, notes)

    # Assert
    assert "# Weekly Summary" in content
    assert "## Summary" in content
    assert summary in content
    assert "## Original Notes" in content