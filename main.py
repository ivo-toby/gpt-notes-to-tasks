"""
Note processing and summarization tool.

This module provides functionality for processing daily notes, weekly summaries,
meeting notes and learning entries. It interfaces with various services to
generate summaries, extract tasks, and manage reminders.
"""

from services.learning_service import LearningService
from services.summary_service import SummaryService
from services.meeting_service import MeetingService
from services.openai_service import OpenAIService
from utils.config_loader import load_config
from utils.cli import setup_argparser


def process_daily_notes(cfg, cli_args):
    """
    Process daily notes to generate summaries and extract tasks.

    Args:
        cfg (dict): Application configuration dictionary
        cli_args (Namespace): Command line arguments

    Returns:
        None
    """
    summary_service = SummaryService(cfg)
    summary_service.process_daily_notes(
        date_str=cli_args.date,
        dry_run=cli_args.dry_run,
        skip_reminders=cli_args.skip_reminders,
        replace_summary=cli_args.replace_summary
    )


def process_weekly_notes(cfg, cli_args):
    """
    Process and generate weekly note summaries.

    Args:
        cfg (dict): Application configuration dictionary
        cli_args (Namespace): Command line arguments

    Returns:
        None
    """
    summary_service = SummaryService(cfg)
    summary_service.process_weekly_notes(
        date_str=cli_args.date,
        dry_run=cli_args.dry_run,
        replace_summary=cli_args.replace_summary
    )


def process_meeting_notes(cfg, cli_args):
    """
    Process daily notes to generate structured meeting notes.

    Args:
        cfg (dict): Application configuration dictionary
        cli_args (Namespace): Command line arguments

    Returns:
        None
    """
    meeting_service = MeetingService(cfg)
    meeting_service.process_meeting_notes(
        date_str=cli_args.date,
        dry_run=cli_args.dry_run
    )


def process_new_learnings(cfg, cli_args):
    """
    Process and extract new learnings from notes.

    Args:
        cfg (dict): Application configuration dictionary
        cli_args (Namespace): Command line arguments

    Returns:
        None
    """
    learning_service = LearningService(
        cfg["learnings_file"], cfg["learnings_output_dir"]
    )
    learning_service.process_new_learnings(
        OpenAIService(api_key=cfg["api_key"], model=cfg["model"])
    )


if __name__ == "__main__":
    parser = setup_argparser()
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
