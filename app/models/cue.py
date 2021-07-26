from pydantic import BaseModel, Field, validator
from typing import Optional, Union
from datetime import datetime, timedelta
from dateparser import parse
from faker import Faker
import random
import json

from app.models.patient.test_results import Test
from app.models.patient.patient import RandomPatient, PatientSchema

CSV_TO_API_FIELD = {
    'Date Completed': 'completedAt',
    'Member ID': 'badgeId',
    'Test ID': 'testID',
    'Test Result': 'result'
}

CueCSV_TO_Test_Field = {'Test ID': 'test_id',
                        'Date Completed': 'test_performed_datetime',
                        'Test Result': 'positive',
                        'Member ID': 'patient_id'}

CueResult_TO_Test_Field = {
    'testId': 'test_id',
    'completedAt': 'test_performed_datetime',
    'testType': 'specimen_type',
    'result': 'positive',

}


class FakeCue:
    def __init__(self, fake_patient: Union[RandomPatient, PatientSchema]):
        fake = Faker()
        self.testId: str = fake.uuid4()
        self.badgeId = fake_patient.patient_id
        self.patient_id = self.badgeId
        self.result = random.choice(['POSITIVE', 'NEGATIVE', 'INVALID', 'CANCELED'])
        self.testType = 'NP-Nasopharyngeal swab'
        self.sendingApplication = 'cue'
        self.notes = 'THIS IS A FAKE RESULT FOR A FAKE PATIENT.'
        random_test = parse(random.choice(fake_patient.test_results)['lab_slip_collection_datetime'])
        self.completedAt = (random_test + timedelta(days=1)).isoformat()

    def json(self):
        return json.loads(json.dumps(vars(self)))


class CueResult(BaseModel):
    testId: Optional[str] = Field(None,
                                  description='Unique field representing a test. This will be unique for every test.')
    badgeId: str = Field(...,
                         description='Alphanumeric field that represents the individual being tested. This would be the external id that would be provided when adding users into the Cue Dashboard. This should be unique across all NBA users being tested.')
    patient_id: Optional[str] = Field(None)

    @validator('patient_id', always=True)
    def map_badge_to_pid(cls, v, values):
        return values['badgeId']

    result: str = Field(...,
                        description='This represents the outcome of a test run on the Cue Health Reader. Possible outcomes include: POSITIVE, NEGATIVE, INVALID, CANCELED')

    @validator('result')
    def validate_result(cls, v):
        vup = v.upper()
        if vup in ['POSITIVE', 'NEGATIVE', 'INVALID', 'CANCELED']:
            return vup
        assert False

    testType: Optional[str] = Field('NP-Nasopharyngeal swab', description='Static field describing the type of test')
    sendingApplication: Optional[str] = Field('Cue', description='Static field describing the sending application.')
    notes: Optional[str] = Field(None,
                                 description='Generic note field providing details about the test result and the cue health platform.')
    completedAt: Optional[str] = Field(datetime.now().isoformat(),
                                       description='Long format date field with UTC offset (00: 00) representing time test was completed.')

    def to_test(self):
        mapped_fields = {CueResult_TO_Test_Field.get(k, k): v for k, v in self.dict().items()}
        return Test(**mapped_fields)
