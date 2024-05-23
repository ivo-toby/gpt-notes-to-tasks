from utils.date_utils import get_date_str
import re
from datetime import datetime
import os


class NotesService:
    def __init__(self, note_file):
        self.note_file = note_file

    def load_notes(self):
        expanded_note_file = os.path.expanduser(self.note_file)
        with open(expanded_note_file, "r") as file:
            return file.read()

    def extract_today_notes(self, notes):
        today_str = get_date_str()
        pattern = re.compile(
            rf"\[{today_str}.*?\].*?(?=\[\d{{4}}-\d{{2}}-\d{{2}}|\Z)", re.DOTALL
        )
        today_notes = pattern.findall(notes)
        return "\n".join(today_notes)

    def extract_weekly_notes(self, notes, start_date, end_date):
        pattern = re.compile(rf"\[{start_date}.*?\].*?(?=\[{end_date}\]|\Z)", re.DOTALL)
        weekly_notes = pattern.findall(notes)
        return "\n".join(weekly_notes)

    def save_meeting_notes(meeting_data, output_dir="MeetingNotes"):
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
        with open(file_path, "w") as file:
            file.write(meeting_notes_content)
