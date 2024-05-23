import argparse
from datetime import datetime
import os
from utils.config_loader import load_config
from utils.file_handler import create_output_dir, load_notes, write_summary_to_file
from utils.date_utils import get_date_str, get_week_range
from services.notes_service import NotesService
from services.openai_service import OpenAIService
from services.reminder_service import ReminderService


def process_daily_notes(config, args):
    notes_service = NotesService(config["daily_notes_file"])
    openai_service = OpenAIService(api_key=config["api_key"], model=config["model"])

    notes = notes_service.load_notes()
    today_notes = notes_service.extract_today_notes(notes)

    if not today_notes:
        print("No notes found for today.")
        return

    result = openai_service.summarize_notes_and_identify_tasks(today_notes)
    summary = result["summary"]
    tasks = result["tasks"]
    tags = result["tags"]

    display_results(summary, tasks, tags)

    if not args.dry_run:
        if not args.skip_reminders:
            add_tasks_to_reminders(tasks)

        write_daily_summary(
            config, summary, tasks, tags, today_notes, args.replace_summary
        )


def process_weekly_notes(config, args):
    notes_service = NotesService(config["daily_notes_file"])
    openai_service = OpenAIService(api_key=config["api_key"], model=config["model"])

    notes = notes_service.load_notes()
    start_date, end_date = get_week_range()

    weekly_notes = notes_service.extract_weekly_notes(notes, start_date, end_date)

    if not weekly_notes:
        print("No notes found for the past week.")
        return

    weekly_summary = openai_service.generate_weekly_summary(weekly_notes)
    accomplishments = openai_service.identify_accomplishments(weekly_notes)
    learnings = openai_service.identify_learnings(weekly_notes)

    display_results(weekly_summary, accomplishments, learnings)

    if not args.dry_run:
        write_weekly_summary(
            config,
            weekly_summary,
            accomplishments,
            learnings,
            weekly_notes,
            args.replace_summary,
        )


def process_meeting_notes(config, args):
    notes_service = NotesService(config["daily_notes_file"])
    openai_service = OpenAIService(api_key=config["api_key"], model=config["model"])

    notes = notes_service.load_notes()
    today_notes = notes_service.extract_today_notes(notes)

    if not today_notes:
        print("No notes found for today.")
        return

    meeting_notes = openai_service.generate_meeting_notes(today_notes)

    if not args.dry_run:
        for meeting in meeting_notes:
            save_meeting_notes(meeting)


def display_results(summary, tasks, tags):
    print("Summary:")
    print(summary)
    print("Tags:")
    print(" ".join([f"#{tag}" for tag in tags]))
    print("Action Items:")
    for task in tasks:
        print(f"- {task}")


def add_tasks_to_reminders(tasks):
    for task in tasks:
        ReminderService.add_to_reminders(task)


def write_daily_summary(config, summary, tasks, tags, today_notes, replace_summary):
    # Prepare the folder structure
    now = datetime.now()
    year = now.strftime("%Y")
    month = now.strftime("%m")
    week_number = now.strftime("%U")
    date_str = get_date_str()

    output_dir = create_output_dir(
        os.path.expanduser(f"{config['daily_output_dir']}/{year}/{month}/{week_number}")
    )
    output_file = os.path.join(output_dir, f"{date_str}.md")

    if replace_summary or not os.path.exists(output_file):
        content = create_daily_summary_content(summary, tasks, tags, today_notes)
    else:
        # Append summary to existing file's content
        with open(output_file, "r") as file:
            existing_content = file.read()
        additional_content = create_daily_summary_content(
            summary, tasks, tags, today_notes
        )
        content = existing_content + "\n\n" + additional_content

    write_summary_to_file(output_file, content)


def write_weekly_summary(
    config, weekly_summary, accomplishments, learnings, weekly_notes, replace_summary
):
    # Prepare the output file path
    start_date, end_date = get_week_range()
    year = start_date.strftime("%Y")
    week_number = start_date.strftime("%U")

    output_dir = create_output_dir(
        os.path.expanduser(f"{config['weekly_output_dir']}/{year}/{week_number}")
    )
    output_file = os.path.join(output_dir, f"week_{week_number}_summary.md")

    if replace_summary or not os.path.exists(output_file):
        content = create_weekly_summary_content(
            weekly_summary, accomplishments, learnings, weekly_notes
        )
    else:
        # Append weekly summary to existing file's content
        with open(output_file, "r") as file:
            existing_content = file.read()
        additional_content = create_weekly_summary_content(
            weekly_summary, accomplishments, learnings, weekly_notes
        )
        content = existing_content + "\n\n" + additional_content

    write_summary_to_file(output_file, content)


def create_daily_summary_content(summary, tasks, tags, today_notes):
    return (
        "# Daily Summary\n\n"
        f"## Summary\n\n{summary}\n\n"
        f"### Tags\n\n{' '.join([f'#{tag}' for tag in tags])}\n\n"
        "## Action Items\n\n"
        + "\n".join(f"- {task}" for task in tasks)
        + "\n\n## Original Notes\n\n"
        f"{today_notes}"
    )


def create_weekly_summary_content(
    weekly_summary, accomplishments, learnings, weekly_notes
):
    return (
        "# Weekly Summary\n\n"
        f"## Summary\n\n{weekly_summary}\n\n"
        "## Accomplishments\n\n"
        + "\n".join(f"- {accomplishment}" for accomplishment in accomplishments)
        + "\n\n## Notable Learnings\n\n"
        + "\n".join(f"- {learning}" for learning in learnings)
        + "\n\n## Original Notes\n\n"
        f"{weekly_notes}"
    )


def save_meeting_notes(meeting_data, output_dir="MeetingNotes"):
    date_str = meeting_data.get("date", datetime.now().strftime("%Y-%m-%d"))
    subject = meeting_data.get("meeting_subject", "meeting").replace(" ", "_").lower()
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
            f"- {action_item}" for action_item in meeting_data.get("action_items", [])
        )
        + "\n\n"
        f"## References\n\n{meeting_data.get('references')}\n"
    )

    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, file_name)
    with open(file_path, "w") as file:
        file.write(meeting_notes_content)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Note Summarizer")
    parser.add_argument(
        "--config", type=str, default="config.yaml", help="Path to configuration file"
    )
    parser.add_argument("--weekly", action="store_true", help="Process weekly notes")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not write to files or create reminders",
    )
    parser.add_argument(
        "--skip-reminders", action="store_true", help="Do not create reminders"
    )
    parser.add_argument(
        "--replace-summary",
        action="store_true",
        help="Replace existing summary instead of appending",
    )
    parser.add_argument(
        "--meetingnotes",
        action="store_true",
        help="Generate and save meeting notes",
    )
    args = parser.parse_args()

    config = load_config(args.config)

    if args.meetingnotes:
        process_meeting_notes(config, args)
    elif args.weekly:
        process_weekly_notes(config, args)
    else:
        process_daily_notes(config, args)

