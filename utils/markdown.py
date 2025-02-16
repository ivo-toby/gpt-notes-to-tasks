"""
Markdown content generation utilities.

This module provides functions for generating formatted markdown content
for various types of notes and summaries.
"""

from datetime import datetime
from typing import List


def create_daily_summary_content(
    summary: str, tasks: List[str], tags: List[str], today_notes: str
) -> str:
    """
    Create formatted content for daily summary markdown file.

    Args:
        summary (str): Generated summary text
        tasks (List[str]): List of identified tasks
        tags (List[str]): List of relevant tags
        today_notes (str): Original notes content

    Returns:
        str: Formatted markdown content
    """
    return (
        "# Daily Summary\n\n"
        f"## Summary\n\n{summary}\n\n"
        f"### Tags\n\n{' '.join([f'#{tag}' for tag in tags])}\n\n"
        "## Action Items\n\n"
        + "\n".join(f"- {task}" for task in tasks)
        + "\n\n## Original Notes\n\n"
        f"{today_notes}"
    )


def create_weekly_summary_content(weekly_summary: str, weekly_notes: str) -> str:
    """
    Create formatted content for weekly summary markdown file.

    Args:
        weekly_summary (str): Generated weekly summary
        weekly_notes (str): Original weekly notes

    Returns:
        str: Formatted markdown content
    """
    return (
        "# Weekly Summary\n\n"
        f"## Summary\n\n{weekly_summary}\n\n"
        "\n\n## Original Notes\n\n"
        f"{weekly_notes}"
    )


def create_meeting_notes_content(meeting_data: dict) -> str:
    """
    Create formatted content for meeting notes markdown file.

    Args:
        meeting_data (dict): Meeting information including subject, participants, etc.

    Returns:
        str: Formatted markdown content
    """
    date_str = meeting_data.get("date", datetime.now().strftime("%Y-%m-%d"))
    return (
        f"# {date_str} Meeting Notes - {meeting_data.get('meeting_subject')}\n\n"
        f"## Tags\n\n{meeting_data.get('tags')}\n\n"
        "## Participants\n\n"
        + "\n".join(
            f"- {participant}" for participant in meeting_data.get("participants", [])
        )
        + "\n\n"
        f"## Meeting notes\n\n{meeting_data.get('meeting_notes')}\n\n"
        "## Decisions\n\n"
        f"{meeting_data.get('decisions', '')}\n\n"
        "## Action items\n\n"
        + "\n".join(
            f"- {action_item}" for action_item in meeting_data.get("action_items", [])
        )
        + "\n\n"
        f"## References\n\n{meeting_data.get('references', '')}\n"
    )
