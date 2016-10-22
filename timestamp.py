import pytz
import dateutil.parser
from datetime import datetime


def datetime_to_unix_timestamp(dt, epoch=dateutil.parser.parse("1970-01-01T00:00:00Z")):
    td = dt - epoch
    return (td.microseconds + (td.seconds + td.days * 86400) * 10**6) / 10**6


def unix_timestamp_diff_minutes(oldtime, newtime):
    return (newtime - oldtime) / 60


def wiki_timestamp_to_datetime(ts):
    ts = ts.split("-")
    year = int(ts[0])
    month = int(ts[1])
    time = ts[2].split("T")
    day = int(time[0])
    time = time[1].split(":")
    hour = int(time[0])
    minute = int(time[1])
    second = int(time[2].strip("Z"))
    return datetime(year, month, day, hour, minute, second, tzinfo=pytz.utc)


# TODO: is this ever called?
def string2date(s):
    """
        month-day-year
    """
    s = s.split('-')
    return datetime(int(s[2]), int(s[0]), int(s[1]), 0, 0, 0)
