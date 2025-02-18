"""
Tests for the NotesService class.

This module contains comprehensive tests for all NotesService functionality
including note extraction, date handling, and file operations.
"""

import os
import pytest
from datetime import datetime, timedelta
from services.notes_service import NotesService

# Test data
SAMPLE_NOTES = """
[2024-02-15 09:00:00 AM] First note for day 1
[2024-02-15 10:00:00 AM] Second note for day 1

[2024-02-16 09:15:00 AM] First note for day 2
[2024-02-16 14:30:00 PM] Second note for day 2
[2024-02-16 17:45:00 PM] Third note for day 2

[2024-02-17 11:00:00 AM] Note for day 3
"""

@pytest.fixture
def notes_file(tmp_path):
    """Create a temporary notes file with sample data."""
    file_path = tmp_path / "test_notes.md"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(SAMPLE_NOTES)
    return str(file_path)

@pytest.fixture
def notes_service(notes_file):
    """Create a NotesService instance with the test file."""
    return NotesService(notes_file)

def test_load_notes(notes_service, notes_file):
    """Test loading notes from file."""
    # Test successful load
    content = notes_service.load_notes()
    assert content == SAMPLE_NOTES

    # Test file not found
    service = NotesService("nonexistent.md")
    with pytest.raises(FileNotFoundError):
        service.load_notes()

    # Test permission error (create readonly file)
    readonly_file = notes_file + ".readonly"
    with open(readonly_file, "w") as f:
        f.write("test")
    os.chmod(readonly_file, 0o000)
    service = NotesService(readonly_file)
    with pytest.raises(PermissionError):
        service.load_notes()
    os.chmod(readonly_file, 0o666)
    os.remove(readonly_file)

def test_extract_today_notes(notes_service):
    """Test extracting notes for a specific date."""
    # Test with specific date
    notes = notes_service.extract_today_notes(SAMPLE_NOTES, "2024-02-16")
    assert "First note for day 2" in notes
    assert "Second note for day 2" in notes
    assert "Third note for day 2" in notes
    assert "First note for day 1" not in notes
    assert "Note for day 3" not in notes

    # Test with yesterday
    today = datetime.now()
    yesterday = (today - timedelta(days=1)).strftime("%Y-%m-%d")
    notes = notes_service.extract_today_notes(SAMPLE_NOTES, "yesterday")
    assert yesterday in notes or not notes  # Notes might be empty if yesterday not in sample

    # Test with today
    notes = notes_service.extract_today_notes(SAMPLE_NOTES, "today")
    today_str = today.strftime("%Y-%m-%d")
    assert today_str in notes or not notes  # Notes might be empty if today not in sample

    # Test with invalid date format
    notes = notes_service.extract_today_notes(SAMPLE_NOTES, "invalid-date")
    assert notes == ""  # Should return empty string for invalid date

def test_extract_weekly_notes(notes_service):
    """Test extracting notes for a week period."""
    # Test with specific date
    week_id, notes = notes_service.extract_weekly_notes(SAMPLE_NOTES, "2024-02-15")
    assert "2024-W07" in week_id  # Feb 15, 2024 is in week 7
    assert "First note for day 1" in notes
    assert "First note for day 2" in notes
    assert "Note for day 3" in notes

    # Test with different days parameter
    week_id, notes = notes_service.extract_weekly_notes(SAMPLE_NOTES, "2024-02-15", days=2)
    assert "First note for day 1" in notes
    assert "First note for day 2" in notes
    assert "Note for day 3" not in notes

    # Test with date having no notes
    week_id, notes = notes_service.extract_weekly_notes(SAMPLE_NOTES, "2024-03-01")
    assert notes == ""

def test_save_meeting_notes(notes_service, tmp_path):
    """Test saving meeting notes to file."""
    output_dir = str(tmp_path / "meeting_notes")

    meeting_data = {
        "date": "2024-02-15",
        "meeting_subject": "Test Meeting",
        "tags": "#test #meeting",
        "participants": ["Alice", "Bob", "Charlie"],
        "meeting_notes": "Discussed test cases",
        "decisions": "Decided to write more tests",
        "action_items": ["Write tests", "Review code"],
        "references": "None"
    }

    # Test successful save
    notes_service.save_meeting_notes(meeting_data, output_dir)
    expected_file = os.path.join(output_dir, "2024-02-15_test_meeting.md")
    assert os.path.exists(expected_file)

    # Verify content
    with open(expected_file, "r", encoding="utf-8") as f:
        content = f.read()
        assert "Test Meeting" in content
        assert "Alice" in content
        assert "Bob" in content
        assert "Charlie" in content
        assert "Discussed test cases" in content
        assert "Write tests" in content
        assert "Review code" in content

    # Test with missing optional fields
    minimal_meeting_data = {
        "meeting_subject": "Minimal Meeting",
        "participants": [],
        "meeting_notes": "Test",
        "tags": "",
        "references": ""
    }
    notes_service.save_meeting_notes(minimal_meeting_data, output_dir)
    today_str = datetime.now().strftime("%Y-%m-%d")
    minimal_file = os.path.join(output_dir, f"{today_str}_minimal_meeting.md")
    assert os.path.exists(minimal_file)

    # Test permission error
    if os.name != "nt":  # Skip on Windows
        os.chmod(output_dir, 0o000)
        with pytest.raises(PermissionError):
            notes_service.save_meeting_notes(meeting_data, output_dir)
        os.chmod(output_dir, 0o755)

if __name__ == "__main__":
    pytest.main([__file__])