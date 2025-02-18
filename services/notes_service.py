"""
Notes processing service.

This module handles loading, extracting, and saving various types of notes
including daily notes, weekly notes, and meeting notes.
"""

import os
import re
from datetime import datetime, timedelta
from typing import Optional, Tuple

from utils.date_utils import get_date_str


class NotesService:
    """
    Service for processing and managing notes.

    This service handles loading notes from files, extracting specific sections
    based on dates, and saving processed notes.
    """

    def __init__(self, note_file: str):
        """
        Initialize the notes service.

        Args:
            note_file (str): Path to the notes file
        """
        self.note_file = note_file

    def load_notes(self) -> str:
        """
        Load notes from the configured file.

        Returns:
            str: Content of the notes file

        Raises:
            FileNotFoundError: If the notes file doesn't exist
            PermissionError: If the file can't be accessed
        """
        expanded_note_file = os.path.expanduser(self.note_file)
        try:
            with open(expanded_note_file, "r", encoding="utf-8") as file:
                return file.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"Notes file not found: {expanded_note_file}")
        except PermissionError:
            raise PermissionError(
                f"Permission denied accessing file: {expanded_note_file}"
            )

    def extract_today_notes(self, notes: str, today_str: Optional[str] = None) -> str:
        """
        Extract notes for a specific date from the content.

        Args:
            notes (str): Full notes content
            today_str (str, optional): Date to extract notes for. Defaults to today.

        Returns:
            str: Notes for the specified date
        """
        # Step 1: Check if `today_str` is not `None`
        if today_str is not None:
            # Step 2: Validate `today_str` as a date string
            try:
                datetime.strptime(today_str, "%Y-%m-%d")
            except ValueError:
                print("Invalid date string. Using today's date instead.")
                today_str = get_date_str()
        else:
            today_str = get_date_str()

        pattern = re.compile(
            rf"\[{today_str}.*?\].*?(?=\[\d{{4}}-\d{{2}}-\d{{2}}|\Z)", re.DOTALL
        )
        today_notes = pattern.findall(notes)
        return "\n".join(today_notes)

    def extract_weekly_notes(
        self, markdown: str, date_str: Optional[str] = None, days: int = 7
    ) -> Tuple[str, str]:
        """
        Extract notes for a week period from the content.

        Args:
            markdown (str): Full notes content
            date_str (str, optional): Start date for the week. Defaults to today.
            days (int, optional): Number of days to include. Defaults to 7.

        Returns:
            Tuple[str, str]: Week identifier and concatenated notes for the week
        """
        if date_str is None:
            date_str = get_date_str()

        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        start_of_week = date_obj - timedelta(days=date_obj.weekday())
        end_of_week = start_of_week + timedelta(days=6)

        iso_year, iso_week, _ = start_of_week.isocalendar()
        week_identifier = f"{iso_year}-W{iso_week:02d}"

        pattern = r"\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} [AP]M)\] (.*?)(?=\[\d{4}-\d{2}-\d{2}|\Z)"
        notes = []
        for match in re.finditer(pattern, markdown, re.DOTALL):
            timestamp, note = match.groups()
            note_date = datetime.strptime(timestamp, "%Y-%m-%d %I:%M:%S %p")
            if start_of_week <= note_date <= end_of_week:
                notes.append(f"{timestamp}: {note.strip()}")

        return week_identifier, "\n".join(notes)

    def save_meeting_notes(
        self, meeting_data: dict, output_dir: str = "MeetingNotes"
    ) -> None:
        """
        Save meeting notes to a markdown file.

        Args:
            meeting_data (dict): Meeting information including subject, participants, etc.
            output_dir (str, optional): Directory to save meeting notes. Defaults to "MeetingNotes".

        Returns:
            None

        Raises:
            PermissionError: If the directory can't be created or file can't be written
        """
        date_str = meeting_data.get("date", datetime.now().strftime("%Y-%m-%d"))
        subject = (
            meeting_data.get("meeting_subject", "meeting").replace(" ", "_").lower()
        )
        file_name = f"{date_str}_{subject}.md"

        meeting_notes_content = (
            f"# {date_str} Meeting Notes - {meeting_data.get('meeting_subject')}\n\n"
            f"## Tags\n\n{meeting_data.get('tags')}\n\n"
            "## Participants\n\n"
            + "\n".join(
                f"- {participant}" for participant in meeting_data.get("participants")
            )
            + "\n\n"
            f"## Meeting notes\n\n{meeting_data.get('meeting_notes')}\n\n"
            "## Decisions\n\n" + f"{meeting_data.get('decisions', '')}\n\n"
            "## Action items\n\n"
            + "\n".join(
                f"- {action_item}"
                for action_item in meeting_data.get("action_items", [])
            )
            + "\n\n"
            f"## References\n\n{meeting_data.get('references')}\n"
        )

        os.makedirs(output_dir, exist_ok=True)
        file_path = os.path.join(output_dir, file_name)
        try:
            with open(file_path, "w", encoding="utf-8") as file:
                file.write(meeting_notes_content)
        except PermissionError:
            raise PermissionError(f"Permission denied writing to file: {file_path}")
