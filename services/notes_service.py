from utils.date_utils import get_date_str
import re
from datetime import datetime, timedelta
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

    def extract_weekly_notes(self, markdown, days=7):
        """
        Fetch notes from the last 'days' days from a markdown string.

        Args:
            markdown (str): Markdown string containing notes and timestamps
            days (int): Number of days to look back from the current date

        Returns:
            list: List of notes from the last 'days' days
        """
        notes = []
        pattern = r"\[(.*?)\] (.*?)(?=\[\d{4}-\d{2}-\d{2}|\Z)"
        for match in re.finditer(pattern, markdown, re.DOTALL):
            timestamp, note = match.groups()
            notes.append((timestamp, note.strip()))

        current_date = datetime.now()
        start_date = current_date - timedelta(days=days)

        recent_notes = [
            f"{timestamp}: {note}"
            for timestamp, note in notes
            if datetime.strptime(timestamp, "%Y-%m-%d %I:%M:%S %p") > start_date
        ]
        return "\n".join(recent_notes)

    def OLDextract_weekly_notes(self, notes, start_date, end_date):
        # Convert the start and end dates to datetime objects
        # Format dates to match the format in the notes
        start_date_formatted = start_date.strftime("%Y-%m-%d")
        end_date_formatted = end_date.strftime("%Y-%m-%d")

        # Adjust the pattern to match the formatted date in notes
        pattern = re.compile(
            rf"\[{start_date_formatted}.*?\](.*?)(?=\[{end_date_formatted}.*?\]|\Z)",
            re.DOTALL,
        )
        # Debugging print statement to check pattern
        print(f"Regex pattern: {pattern}")

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
