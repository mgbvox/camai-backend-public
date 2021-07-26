from pydantic import BaseModel, Field, validator, root_validator
from typing import Optional, Union
from datetime import datetime, timedelta
from dateparser import parse
from faker import Faker
import random
import json
from datetime import datetime

from app.utils.datetimes import to_dt, to_timestamp

class DateRange(BaseModel):
    start_datetime: Union[str, datetime] = Field(to_dt('1/01/1000'), description='The start of the date range.')
    end_datetime: Union[str, datetime] = Field(to_dt('now'), description='The end of the date range.')

    # Validate these!
    @root_validator(pre=True)
    def ensure_all_are_datetime(cls, values):
        formatted_values = dict()
        for k,v in values.items():
            assert to_dt(v) is not None
            formatted_values[k] = to_dt(v)
        return formatted_values

    @root_validator
    def ensure_end_follows_start(cls, values):
        if values['end_datetime'] < values['start_datetime']:
            raise ValueError('End must occur after Start!')
        return values