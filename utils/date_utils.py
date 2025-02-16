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


def get_week_range() -> Tuple[datetime, datetime]:
    """
    Get the start and end dates of the current week.

    The week is considered to start on Monday (0) and end on Sunday (6).

    Returns:
        Tuple[datetime, datetime]: Tuple containing (start_of_week, end_of_week)
    """
    today = datetime.now()
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    return start_of_week, end_of_week


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
