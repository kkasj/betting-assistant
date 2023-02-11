from datetime import datetime, timedelta
from typing import List

def days_list_dbformat(start_day: str, end_day: str):
    start_day = datetime(*map(int, start_day.split('_')))
    end_day = datetime(*map(int, end_day.split('_')))
    d = (end_day - start_day).days
    d2str = lambda x: '_'.join(map(str, (x.year, x.month, x.day)))
    return [d2str(start_day + k * timedelta(days=1)) for k in range(d+1)]

def datetime2str_dbformat(date: datetime) -> str:
    """
    Return a string representation of a date in "Y_M_D" format.
    """
    return f"{date.year}_{date.month}_{date.day}"



def str2datetime(date: str) -> datetime:
    """
    Return a datetime object based on a date in "Y,M,D,H,m" string format.
    """

    return datetime(*[int(elem) for elem in date.split(',')])


def datetime2str(date: datetime) -> str:
    """
    Return a date in "Y,M,D,H,m" string format based on a datetime object.
    """

    return ','.join(map(str, [date.year, date.month, date.day, date.hour, date.minute]))


def latest_date_str(dates_str = List[str]) -> str:
    """
    Return the latest date out of a list of dates given in "Y,M,D,H,m" string format.
    """

    datetimes = [str2datetime(date_str) for date_str in dates_str]

    return datetime2str(max(datetimes))

def later_date_str(date1: str, date2: str) -> bool:
    """
    Return True if date2 is later, False otherwise.
    """

    return str2datetime(date1) < str2datetime(date2)