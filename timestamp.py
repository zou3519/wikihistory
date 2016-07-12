from datetime import datetime, timedelta

def time_diff(oldTime, newTime):
    """
        Finds the time difference in minutes between 2 strings 
            in Wikipedia timestamp format.
    """
    MINTIME = 0.01

    oldTime=oldTime.split("-")
    oyear= int(oldTime[0])
    omonth=int(oldTime[1])
    odt=oldTime[2].split("T")
    oday=int(odt[0])
    odt=odt[1].split(":")
    ohour=int(odt[0])
    ominute = int(odt[1])
    osecond=int(odt[2].strip("Z"))

    newTime=newTime.split("-")
    nyear= int(newTime[0])
    nmonth=int(newTime[1])
    ndt=newTime[2].split("T")
    nday=int(ndt[0])
    ndt=ndt[1].split(":")
    nhour=int(ndt[0])
    nminute = int(ndt[1])
    nsecond=int(ndt[2].strip("Z"))


    oDate=datetime(oyear, omonth, oday, ohour, ominute, osecond)
    nDate=datetime(nyear, nmonth, nday, nhour, nminute, nsecond)

    delta=nDate-oDate
    minutes= float(delta.total_seconds())/60
    if minutes==0:
        minutes=MINTIME
    return minutes
