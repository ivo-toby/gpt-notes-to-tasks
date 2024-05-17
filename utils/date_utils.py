from datetime import datetime, timedelta


def get_date_str(date=None):
    date = date or datetime.now()
    return date.strftime("%Y-%m-%d")


def get_week_range():
    today = datetime.now()
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    return start_of_week, end_of_week


def get_time_str(date=None):
    date = date or datetime.now()
    return date.strftime("%H:%M:%S %p")
