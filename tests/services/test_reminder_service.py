"""
Tests for the reminder service.

This module contains tests for the reminder service functionality,
including adding tasks to macOS Reminders app.
"""

from unittest.mock import patch

import pytest

from services.reminder_service import ReminderService


@pytest.fixture
def sample_task():
    """Return a sample task for testing."""
    return "Test task: Implement new feature"


def test_add_to_reminders_success(sample_task):
    """Test successful addition of a reminder with user confirmation."""
    with patch("builtins.input", return_value="y"), \
         patch("applescript.run", return_value=True), \
         patch("builtins.print") as mock_print:

        # Execute
        result = ReminderService.add_to_reminders(sample_task)

        # Assert
        assert result is True
        mock_print.assert_called_with(f"Task '{sample_task}' added to Work list in Reminders.")


def test_add_to_reminders_user_declines(sample_task):
    """Test reminder addition when user declines."""
    with patch("builtins.input", return_value="n"), \
         patch("applescript.run") as mock_run, \
         patch("builtins.print") as mock_print:

        # Execute
        result = ReminderService.add_to_reminders(sample_task)

        # Assert
        assert result is False
        mock_run.assert_not_called()
        mock_print.assert_called_with("Task not added to reminders.")


def test_add_to_reminders_applescript_failure(sample_task):
    """Test reminder addition when AppleScript fails."""
    with patch("builtins.input", return_value="y"), \
         patch("applescript.run", return_value=False), \
         patch("builtins.print") as mock_print:

        # Execute
        result = ReminderService.add_to_reminders(sample_task)

        # Assert
        assert result is False
        mock_print.assert_called_with("Failed to add task to Reminders.")


def test_add_to_reminders_exception(sample_task):
    """Test reminder addition when an exception occurs."""
    with patch("builtins.input", return_value="y"), \
         patch("applescript.run", side_effect=Exception("Test error")), \
         patch("builtins.print") as mock_print:

        # Execute
        result = ReminderService.add_to_reminders(sample_task)

        # Assert
        assert result is False
        mock_print.assert_called_with("Error adding reminder: Test error")


def test_add_to_reminders_script_content(sample_task):
    """Test that the AppleScript content is correctly formatted."""
    expected_script = f"""
            tell application "Reminders"
                try
                    set mylist to list "Work"
                    tell mylist
                        make new reminder with properties {{name:"{sample_task}"}}
                    end tell
                    return true
                on error errMsg
                    return false
                end try
            end tell
            """

    with patch("builtins.input", return_value="y"), \
         patch("applescript.run") as mock_run, \
         patch("builtins.print"):

        # Execute
        ReminderService.add_to_reminders(sample_task)

        # Assert
        mock_run.assert_called_once_with(expected_script)