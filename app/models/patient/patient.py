import datetime
from typing import Optional, List, Type
from pydantic import BaseModel, Field, validator
from pydantic.fields import ModelField
import random
from faker import Faker
import json
from dateparser import parse
import regex as re

from app.database.crypto import hash_string

from app.models.patient.test_results import Test, FakeTest
from app.models.patient.address import Address, FakeAddress
from app.core.globals import NAME_TO_CODE, FISHERY_NAMES, TRUE_ANALOGS
from app.utils.sms import alert_sms

import asyncio


class RandomPatient:
    def __init__(self, is_lab_slip=True, n_tests=None):
        self.is_lab_slip = is_lab_slip
        fake = Faker()
        self.last_name = 'TEST_' + fake.last_name()
        self.first_name = 'TEST_' + fake.first_name()

        dob = fake.date_of_birth()
        self.dob: str = dob.isoformat()
        self.ssn: str = fake.ssn()
        self.gender: str = random.choice(['M', 'F'])
        self.race_ethnicity: str = random.choice(['Indigo', 'Violet', 'UltraAwesome'])
        self.hispanic: str = random.choice(['Y', 'N'])

        self.home_phone = fake.phone_number()
        self.cell_phone = fake.phone_number()
        self.local_phone = fake.phone_number()

        self.physical_address: FakeAddress = FakeAddress().json()
        self.email_address: str = fake.email()
        self.base_email_hash: str = hash_string(self.email_address)

        self.fishery_name = random.choice(FISHERY_NAMES)
        self.fishery_id = NAME_TO_CODE[self.fishery_name]

        self.insurance: str = random.choice(['Y', 'N'])
        self.been_here_before: str = random.choice(['Y', 'N'])

        if n_tests:
            self.test_results: List[FakeTest] = [FakeTest(lab_slip=self.is_lab_slip).json() for _ in
                                                 range(n_tests)]
        else:
            self.test_results: List[FakeTest] = [FakeTest(lab_slip=self.is_lab_slip).json() for _ in
                                                 range(random.randint(1, 5))]

        # DERIVED FIELDS
        self.patient_id = str(self.fishery_id).zfill(2) + self.last_name.upper()[:1] + self.first_name.upper()[
                                                                                       :1] + str(dob.month).zfill(
            2) + str(dob.day).zfill(2) + str(dob.year).zfill(2)  # + 'S' + str(self.ssn[-4:])

        self.pid_hash = hash_string(self.patient_id)

    def __repr__(self):
        return self.first_name + ' ' + self.last_name

    def json(self):
        return json.loads(json.dumps(vars(self)))

    def iso_to_date_triple(self, iso: str, prefix: str):
        dt: datetime.datetime = parse(iso)
        m = dt.month
        d = dt.day
        y = dt.year
        return {f'{prefix}_month': str(m),
                f'{prefix}_day': str(d),
                f'{prefix}_year': str(y)}

    def to_form_fields(self):
        data = self.json()
        data.update(self.iso_to_date_triple(data.pop('dob'), prefix='dob'))
        test = data.pop('test_results')[0]

        data.update(self.iso_to_date_triple(test['lab_slip_collection_datetime'], prefix='collection'))
        data['positive'] = random.choice(['POSITIVE', 'NEGATIVE'])
        # Map address
        phys_address = data.pop('physical_address')
        data.update(phys_address)

        data.pop('fishery_id')
        data.pop('is_lab_slip')

        return data

    def fake_cue(self):
        fake = Faker()
        slip_datetime = parse(self.test_results[0]['lab_slip_collection_datetime'])
        return {'Member Name': self.full_name(),
                'Date Completed': (
                        slip_datetime + datetime.timedelta(minutes=random.randint(200, 2000))).isoformat(),
                'Member ID': self.patient_id,
                'Member DOB': self.dob,
                'Test ID': fake.uuid4(),
                'Test Result': random.choice(['POSITIVE', 'NEGATIVE']),
                'Sample ID': fake.uuid4(),
                }

    def full_name(self):
        return self.first_name + ' ' + self.last_name


def string_to_bool(s: str) -> bool:
    boolified = s in TRUE_ANALOGS
    return boolified


class PatientSchema(BaseModel):
    # Identifying Info
    last_name: str = Field(...)
    first_name: str = Field(...)
    ssn: Optional[str] = Field(None, description='Patient Social Security Number, if exists.')
    dob: str = Field(..., description='Patient date of birth.')

    # Demographics
    gender: Optional[str] = Field(None)

    race_ethnicity: Optional[str] = Field('Declined to state', description='Patient race and/or ethnicity.')
    hispanic: str = Field(..., description='Whether or not patient identifies as hispanic.')
    # _hispanic_to_bool = validator('hispanic', allow_reuse=True)(string_to_bool)

    # Contact Info
    home_phone: Optional[str] = Field(None)
    cell_phone: Optional[str] = Field(None)
    local_phone: Optional[str] = Field(None)
    physical_address: Optional[Address] = Field(None, description='Address object of patient.')
    email_address: Optional[str] = Field(None, description='Formatted email address.')

    @validator('email_address')
    def clean_email(cls, v):
        # insane pattern from https://emailregex.com/; adapted for python.
        email_pat = r"REDACTED"
        pat = re.compile(email_pat)
        lower = v.lower().strip()
        # Find all email matches in string - there may be multiple.
        # Only use the first.
        email = re.findall(pat, lower)[0]
        return email

    base_email_hash: Optional[str] = Field(None, description='Hash of the base email (without +N) for search.')

    @validator('base_email_hash')
    def hash_email(cls, v, values):
        addr = values.get('email_address')
        if addr:
            hashed = hash_string(addr)
            return hashed

    # Health Info
    insurance: str = Field(..., description='Whether patient is insured.')
    been_here_before: str = Field(..., description='Has the patient been to Camai CHC before?')

    fishery_name: str = Field(..., description='Name of Fishery.')  # e.g. Silver Bay

    fishery_id: Optional[str] = Field(None, description='Fishery ID - should be derived from fishery_name')  # e.g. 01

    @validator('fishery_id')
    def derive_fishery_id(cls, v, values):
        '''CODE REDACTED FOR CONFIDENTIALITY'''
        return '33'

    # Test Results
    test_results: Optional[List[Test]] = Field([], description="Test results, if any, for this patient.")

    patient_id: Optional[str] = Field(None,
                                      description='Patient ID; must be validated against db afterwards.')



    @validator('patient_id')
    def derive_pid(cls, v, values):
        '''CODE REDACTED FOR CONFIDENTIALITY'''
        return 'NOTANID'

    pid_hash: Optional[str] = Field(None,
                                    description='Patient ID HASH - for lookup.')

    @validator('pid_hash', always=True)
    def hash_pid(cls, v, values):
        if values.get('patient_id'):
            return hash_string(values['patient_id'])
        return None


    class Config:
        schema_extra = {
            "example": RandomPatient().json()
        }


def ResponseModel(data, message):
    return {
        "data": [data],
        "code": 200,
        "message": message,
    }


def ErrorResponseModel(error, code, message):
    loop = asyncio.get_running_loop()
    loop.create_task(alert_sms(body=message))
    return {"error": error, "code": code, "message": message}
