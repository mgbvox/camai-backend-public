import dateparser
import datetime
import pytz
from typing import Optional, Union
from pydantic import BaseModel, Field, validator, root_validator
import random
from faker import Faker
from datetime import timedelta
import json
import arrow

from app.core.globals import CUE_TEST_FIELDS
from app.utils.datetimes import to_timestamp, to_dt

DATETIME_FIELDS = ['lab_slip_collection_datetime', 'test_performed_datetime', 'test_reported_datetime']


class FakeTest:
    def __init__(self, lab_slip=False):
        fake = Faker()
        slip_datetime = fake.date_time()
        if lab_slip:
            # Lab Slip Order Form data
            self.specimen_type: str = 'NP-Nasopharyngeal swab'
            self.lab_slip_collection_datetime: str = slip_datetime.isoformat()
        else:
            # Result data
            # All optional, as there will be some delay between PDF upload and test result upload
            self.test_id: str = fake.uuid4()
            self.test_performed_datetime: str = (
                    slip_datetime + timedelta(minutes=random.randint(200, 2000))).isoformat()
            self.test_reported_datetime: str = (
                    slip_datetime + timedelta(minutes=random.randint(2050, 3000))).isoformat()

            self.positive: str = random.choice(['POSITIVE', 'NEGATIVE'])

    def json(self):
        return json.loads(json.dumps(vars(self)))




def field_exists(value):
    return (value is not None) or bool(value)


class Test(BaseModel):
    '''
    A single SARS-COV2 test object.
    '''
    # Collection Data
    specimen_type: str = 'NP-Nasopharyngeal swab'
    # Date and time of test order, as listed on lab slip PDF.
    lab_slip_collection_datetime: Optional[str]

    # Result data
    # All optional, as there will be some delay between PDF upload and test result upload
    # Identifying Info
    test_id: Optional[str]  # EITHER: Cue test_id or AK State Lab ID.

    test_performed_datetime: Optional[str]  # 'Datetime that test was performed.

    test_reported_datetime: Optional[
        str]  # 'Datetime of test result upload to this system. Either via CSV, OCR, or (eventual) API.

    @validator(*DATETIME_FIELDS)
    def to_iso(cls, v):
        try:
            if v:
                aware_dt = arrow.get(v).astimezone(pytz.utc)
                iso_format = aware_dt.isoformat()
                return iso_format
        except:
            return None

    positive: Optional[str]  # 'Whether patient tested positive.

    @validator('positive', always=False)
    def positive_is_valid_term(cls, v) -> str:
        if v:
            v = v.upper()
            if v in ['POSITIVE', 'NEGATIVE', 'INVALID', 'CANCELED', 'NOT TESTED']:
                return v
        return None

    class Config:
        schema_extra = {
            "example": FakeTest().json()
        }

    def cast_dates_to_dt(self):
        for f in DATETIME_FIELDS:
            setattr(self, f, to_dt(getattr(self, f)))

    def cast_dates_to_iso_string(self):
        for f in DATETIME_FIELDS:
            setattr(self, f, getattr(self, f).isoformat())


class TestStrict(Test):
    @validator('lab_slip_collection_datetime')
    def ensure_lab_collection_dt_exists(cls, v):
        assert v is not None
        return v

    @root_validator(pre=False)
    def ensure_dates_follow_correct_sequence(cls, values):
        lab_dt = to_dt(values.get('lab_slip_collection_datetime'))
        performed = to_dt(values.get('test_performed_datetime'))
        reported = to_dt(values.get('test_reported_datetime'))
        if performed and reported:
            in_sequence = all(
                [lab_dt <= performed, performed <= reported, reported <= arrow.now().astimezone(pytz.utc)])
            assert in_sequence
        return values

    @root_validator(pre=False)
    def ensure_result_included_if_test_complete(cls, values):
        performed = to_dt(values.get('test_performed_datetime'))
        reported = to_dt(values.get('test_reported_datetime'))
        if performed and reported:
            assert values['positive'] != None
        return values


    @root_validator(pre=False)
    def ensure_all_fields_present_if_test_complete(cls, values):

        cue_data_exists = any([field_exists(values.get(k)) for k in CUE_TEST_FIELDS])
        all_data_complete = all([field_exists(values.get(k)) for k in values.keys()])

        if cue_data_exists:
            assert all_data_complete
        else:
            assert not cue_data_exists

        return values

