"""
Tests for date utilities.

This module contains tests for date-related utility functions.
"""

from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from utils.date_utils import get_date_str, get_week_dates


def test_get_date_str():
    """Test getting date string for a specific date."""
    # Setup
    test_date = datetime(2024, 2, 18)

    with patch("utils.date_utils.datetime") as mock_datetime:
        mock_datetime.now.return_value = test_date
        mock_datetime.strftime = datetime.strftime

        # Execute
        result = get_date_str()

        # Assert
        assert result == "2024-02-18"


def test_get_week_dates():
    """Test getting start and end dates for a week."""
    # Setup
    test_date = datetime(2024, 2, 12)  # A Monday

    # Execute
    start_date, end_date = get_week_dates(test_date)

    # Assert
    assert start_date == datetime(2024, 2, 12)  # Monday
    assert end_date == datetime(2024, 2, 18)  # Sunday


def test_get_week_dates_mid_week():
    """Test getting week dates when input is mid-week."""
    # Setup
    test_date = datetime(2024, 2, 14)  # A Wednesday

    # Execute
    start_date, end_date = get_week_dates(test_date)

    # Assert
    assert start_date == datetime(2024, 2, 12)  # Monday
    assert end_date == datetime(2024, 2, 18)  # Sunday


def test_get_week_dates_sunday():
    """Test getting week dates when input is a Sunday."""
    # Setup
    test_date = datetime(2024, 2, 18)  # A Sunday

    # Execute
    start_date, end_date = get_week_dates(test_date)

    # Assert
    assert start_date == datetime(2024, 2, 12)  # Monday
    assert end_date == datetime(2024, 2, 18)  # Sunday


def test_get_week_dates_default():
    """Test getting week dates with default current date."""
    # Setup
    test_date = datetime(2024, 2, 12)  # A Monday

    with patch("utils.date_utils.datetime") as mock_datetime:
        mock_datetime.now.return_value = test_date
        # Make the mock class behave like the real datetime for class methods
        mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)

        # Execute
        start_date, end_date = get_week_dates()

        # Assert
        assert start_date == datetime(2024, 2, 12)  # Monday
        assert end_date == datetime(2024, 2, 18)  # Sunday