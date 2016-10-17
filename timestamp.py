from datetime import datetime, timedelta


def time_diff(oldTime, newTime):
    """
        Finds the time difference in minutes between 2 strings 
            in Wikipedia timestamp format.
    """
    oDate = ts2date(oldTime)
    nDate = ts2date(newTime)
    delta = nDate - oDate
    minutes = float(delta.total_seconds()) / 60

    return minutes


def ts2date(ts):
    """
    """
    ts = ts.split("-")
    year = int(ts[0])
    month = int(ts[1])
    time = ts[2].split("T")
    day = int(time[0])
    time = time[1].split(":")
    hour = int(time[0])
    minute = int(time[1])
    second = int(time[2].strip("Z"))

    return datetime(year, month, day, hour, minute, second)


def string2date(s):
    """
        month-day-year
    """
    s = s.split('-')
    return datetime(int(s[2]), int(s[0]), int(s[1]), 0, 0, 0)
