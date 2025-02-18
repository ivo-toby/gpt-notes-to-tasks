"""
Date and time utility functions.

This module provides helper functions for date and time operations,
including date string formatting and week range calculations.
"""

from datetime import datetime, timedelta
from typing import Optional, Tuple


def get_date_str(date: Optional[datetime] = None) -> str:
    """
    Get date string in YYYY-MM-DD format.

    Args:
        date (datetime, optional): Date to format. Defaults to current date/time.

    Returns:
        str: Formatted date string
    """
    date = date or datetime.now()
    return date.strftime("%Y-%m-%d")


def get_week_dates(date: Optional[datetime] = None) -> Tuple[datetime, datetime]:
    """
    Get the start and end dates of the week containing the given date.

    The week is considered to start on Monday (0) and end on Sunday (6).
    All times are set to midnight (00:00:00) for consistency.

    Args:
        date (datetime, optional): Date within the desired week. Defaults to current date.

    Returns:
        Tuple[datetime, datetime]: Tuple containing (start_of_week, end_of_week)
    """
    # Get current date if none provided
    if date is None:
        date = datetime.now()

    # Normalize to midnight
    date = datetime(date.year, date.month, date.day)

    # Calculate days to subtract to get to Monday (weekday() returns 0 for Monday)
    days_to_monday = date.weekday()

    # Get Monday (start of week)
    start_date = date - timedelta(days=days_to_monday)

    # Get Sunday (end of week)
    end_date = start_date + timedelta(days=6)

    return start_date, end_date


def get_time_str(date: Optional[datetime] = None) -> str:
    """
    Get time string in HH:MM:SS AM/PM format.

    Args:
        date (datetime, optional): Date/time to format. Defaults to current date/time.

    Returns:
        str: Formatted time string
    """
    date = date or datetime.now()
    return date.strftime("%H:%M:%S %p")
