"""
Meeting notes service.

This module handles the generation and storage of meeting notes extracted from daily notes.
"""

import os
from datetime import datetime
from typing import Dict, Optional

from services.notes_service import NotesService
from services.openai_service import OpenAIService
from utils.file_handler import create_output_dir, write_summary_to_file
from utils.markdown import create_meeting_notes_content


class MeetingService:
    def __init__(self, config: Dict):
        """
        Initialize the meeting service.

        Args:
            config (Dict): Application configuration
        """
        self.config = config
        self.notes_service = NotesService(config["daily_notes_file"])
        self.openai_service = OpenAIService(
            api_key=config["api_key"], model=config["model"]
        )

    def process_meeting_notes(
        self, date_str: Optional[str] = None, dry_run: bool = False
    ) -> None:
        """
        Process daily notes to generate structured meeting notes.

        Args:
            date_str (str, optional): Date to process notes for. Defaults to None.
            dry_run (bool): If True, don't write files

        Returns:
            None
        """
        notes = self.notes_service.load_notes()
        today_notes = self.notes_service.extract_today_notes(notes, date_str)

        if not today_notes:
            print("No notes found for today.")
            return

        meeting_notes = self.openai_service.generate_meeting_notes(today_notes)

        if not dry_run:
            for meeting in meeting_notes.get("meetings", []):
                self._save_meeting_notes(meeting)
        else:
            for meeting in meeting_notes.get("meetings", []):
                print(meeting)

    def _save_meeting_notes(
        self, meeting_data: Dict, output_dir: Optional[str] = None
    ) -> None:
        """
        Save meeting notes to a markdown file.

        Args:
            meeting_data (Dict): Meeting information including subject, participants, etc.
            output_dir (str, optional): Override default output directory. Defaults to None.

        Returns:
            None
        """
        output_dir = output_dir or self.config["meeting_notes_output_dir"]
        date_str = meeting_data.get("date", datetime.now().strftime("%Y-%m-%d"))
        subject = (
            meeting_data.get("meeting_subject", "meeting").replace(" ", "_").lower()
        )
        file_name = f"{date_str}_{subject}"

        content = create_meeting_notes_content(meeting_data)

        output_dir = create_output_dir(os.path.expanduser(f"{output_dir}"))
        output_file = os.path.join(output_dir, f"{file_name}.md")

        write_summary_to_file(output_file, content)
