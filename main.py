import argparse
import os
from datetime import datetime, timedelta

from services.learning_service import LearningService
from services.notes_service import NotesService
from services.openai_service import OpenAIService
from services.reminder_service import ReminderService
from utils.config_loader import load_config
from utils.date_utils import get_date_str
from utils.file_handler import create_output_dir, write_summary_to_file


def process_daily_notes(config, args):
    notes_service = NotesService(config["daily_notes_file"])
    openai_service = OpenAIService(api_key=config["api_key"], model=config["model"])

    notes = notes_service.load_notes()
    today_notes = notes_service.extract_today_notes(notes, args.date)

    if not today_notes:
        print("No notes found for today.")
        return
    result = openai_service.summarize_notes_and_identify_tasks(today_notes)
    summary = result["summary"]
    tasks = result["actionable_items"]
    tags = result["tags"]

    display_results(summary, tasks, tags)

    if not args.dry_run:
        if not args.skip_reminders:
            add_tasks_to_reminders(tasks)

        write_daily_summary(
            config, summary, tasks, tags, today_notes, args.replace_summary, args.date
        )


def process_weekly_notes(config, args):
    notes_service = NotesService(config["daily_notes_file"])
    openai_service = OpenAIService(api_key=config["api_key"], model=config["model"])

    notes = notes_service.load_notes()
    weekly_notes = notes_service.extract_weekly_notes(notes, args.date)
    if not weekly_notes:
        print("No notes found for the past week.")
        return

    weekly_summary = openai_service.generate_weekly_summary(weekly_notes)

    display_results(weekly_summary, "", "")

    if not args.dry_run:
        write_weekly_summary(
            config,
            weekly_summary,
            weekly_notes,
            args.replace_summary,
            date_str=args.date,  # Ensure date_str is passed here
        )


def process_meeting_notes(config, args):
    notes_service = NotesService(config["daily_notes_file"])
    openai_service = OpenAIService(api_key=config["api_key"], model=config["model"])

    notes = notes_service.load_notes()
    today_notes = notes_service.extract_today_notes(notes, args.date)

    if not today_notes:
        print("No notes found for today.")
        return

    meeting_notes = openai_service.generate_meeting_notes(today_notes)
    if not args.dry_run:
        for meeting in meeting_notes["meetings"]:
            save_meeting_notes(meeting, config["meeting_notes_output_dir"])
    else:
        for meeting in meeting_notes["meetings"]:
            print(meeting)


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


def write_daily_summary(
    config, summary, tasks, tags, today_notes, replace_summary, today_str
):
    # Prepare the folder structure
    if today_str is not None:
        # Step 2: Validate `today_str` as a date string
        try:
            datetime.strptime(today_str, "%Y-%m-%d")
        except ValueError:
            print("Invalid date string. Using today's date instead.")
            today_str = get_date_str()
    else:
        today_str = get_date_str()

    # now = datetime.now()
    now = datetime.strptime(today_str, "%Y-%m-%d")
    year = now.strftime("%Y")
    month = now.strftime("%m")
    week_number = now.strftime("%U")
    # date_str = get_date_str()

    output_dir = create_output_dir(
        os.path.expanduser(f"{config['daily_output_dir']}/{year}/{month}/{week_number}")
    )
    output_file = os.path.join(output_dir, f"{today_str}.md")

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
    config, weekly_summary, weekly_notes, replace_summary, date_str=None
):
    # Determine the date to use
    if date_str:
        current_date = datetime.strptime(date_str, "%Y-%m-%d")
    else:
        current_date = datetime.now()

    # Calculate the start of the week (Monday)
    start_date = current_date - timedelta(days=current_date.weekday())
    end_date = start_date + timedelta(days=6)

    # Get ISO year and week number
    iso_year, iso_week, _ = start_date.isocalendar()
    week_identifier = f"{iso_year}-W{iso_week:02d}"

    # Debug prints
    print(f"DEBUG: start_date = {start_date}")
    print(f"DEBUG: end_date = {end_date}")
    print(f"DEBUG: iso_year = {iso_year}")
    print(f"DEBUG: iso_week = {iso_week}")
    print(f"DEBUG: week_identifier = {week_identifier}")

    # Prepare the output file path
    output_dir = create_output_dir(
        os.path.expanduser(f"{config['weekly_output_dir']}/{iso_year}/{iso_week:02d}")
    )
    output_file = os.path.join(output_dir, f"week_{week_identifier}_summary.md")

    if replace_summary or not os.path.exists(output_file):
        content = create_weekly_summary_content(weekly_summary, weekly_notes)
    else:
        # Append weekly summary to existing file's content
        with open(output_file, "r") as file:
            existing_content = file.read()
        additional_content = create_weekly_summary_content(weekly_summary, weekly_notes)
        content = existing_content + "\n\n" + additional_content

    # Add date range to the content
    date_range = f"# Weekly Summary: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}\n\n"
    content = date_range + content

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


def create_weekly_summary_content(weekly_summary, weekly_notes):
    return (
        "# Weekly Summary\n\n"
        f"## Summary\n\n{weekly_summary}\n\n" + "\n\n## Original Notes\n\n"
        f"{weekly_notes}"
    )


def process_new_learnings(config, args):
    learning_service = LearningService(
        config["learnings_file"], config["learnings_output_dir"]
    )
    openai_service = OpenAIService(api_key=config["api_key"], model=config["model"])

    print("Starting process_new_learnings")
    learning_service.process_new_learnings(openai_service)
    print("DEBUG: Finished process_new_learnings")


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
    output_dir = create_output_dir(os.path.expanduser(f"{output_dir}"))
    output_file = os.path.join(output_dir, f"{file_name}.md")

    os.makedirs(output_dir, exist_ok=True)
    with open(output_file, "w") as file:
        file.write(meeting_notes_content)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Note Summarizer and Learning Processor"
    )
    parser.add_argument(
        "--date",
        type=str,
        help="Date to fetch notes from (or start date for weekly notes)",
    )
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
    parser.add_argument(
        "--process-learnings", action="store_true", help="Process new learnings"
    )
    args = parser.parse_args()

    config = load_config(args.config)
    if args.process_learnings:
        process_new_learnings(config, args)
    elif args.meetingnotes:
        process_meeting_notes(config, args)
    elif args.weekly:
        process_weekly_notes(config, args)
    else:
        process_daily_notes(config, args)
        process_meeting_notes(config, args)
        process_new_learnings(config, args)
