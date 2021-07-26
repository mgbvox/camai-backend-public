import arrow
import pytz
from dateparser import parse

def to_dt(iso):
    try:
        #Try to convert using arrow
        dt = arrow.get(iso).astimezone(pytz.utc)
        return dt
    except:
        #Try to convert using dateparser
        try:
            dt = parse(iso).astimezone(pytz.utc)
            return dt
        except:
            return None

def to_timestamp(dt):
    try:
        ts = dt.timestamp()
        return ts
    except:
        return None