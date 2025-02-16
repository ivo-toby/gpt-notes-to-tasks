"""
Command line interface configuration.

This module handles the setup and parsing of command line arguments.
"""

import argparse


def setup_argparser() -> argparse.ArgumentParser:
    """
    Configure and return the argument parser for the application.

    Returns:
        argparse.ArgumentParser: Configured argument parser
    """
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
    return parser
