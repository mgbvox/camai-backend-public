    import pathlib
from pathlib import Path
import os
from typing import List
from app.core.types import Json

APP_ROOT: pathlib.Path = Path(os.path.realpath(__file__)).parent.parent

NAME_TO_CODE = {'redacted':'redacted'}

CODE_TO_NAME = {v: k for k, v in NAME_TO_CODE.items()}

FISHERY_NAMES = list(NAME_TO_CODE.keys())

'''
Boolean Conversions
'''
_true_strings = 'y yes okay ok correct affirmative confirmed true'.split()
TRUE_ANALOGS = _true_strings + [i.upper() for i in _true_strings]

_false_strings = '--- no incorrect declined false'.split()
FALSE_ANALOGS = _false_strings + [i.upper() for i in _false_strings]

'''
CUE IO
'''

# LET CECELIA KNOW IF CHANGING
PATIENT_EXPORT_FIELDS = [
    'first_name',
    'last_name',
    'email_address',
    'patient_id',
    'home_phone',
    ['physical_address', 'state'],
    'race_ethnicity',
    'gender',
    'race_ethnicity',
    ['physical_address', 'street'],
    ['physical_address', 'city'],
    ['physical_address', 'zip'],
    'dob'
]

CUE_IMPORT_FIELDS = ['firstname',
                     'lastname',
                     'email',
                     'id',
                     'phone',
                     'stateOfResidence',
                     'race',
                     'gender',
                     'ethnicity',
                     'street',
                     'city',
                     'zip',
                     'dateOfBirth']

CUE_TEST_FIELDS = ['test_id', 'test_performed_datetime', 'test_reported_datetime', 'positive']

'''
AK State IO
'''
AK_EXPORT_COLUMNS: List[str] = ['reportingOrganizationCode',
                                'reportingOrganizationDescription',
                                'firstName',
                                'middleName',
                                'lastName',
                                'dateOfBirth',
                                'patientSex',
                                'race',
                                'ethnicity',
                                'street',
                                'city',
                                'state',
                                'zip',
                                'patientPhone',
                                'accessionNumber',
                                'specimenCollectionDate',
                                'specimenAnalysisDate',
                                'orderedTestCode',
                                'orderedTestDescription',
                                'orderedTestCodingSystem',
                                'resultedTestName',
                                'resultedTestCode',
                                'resultedTestCodingSystem',
                                'resultedTestResult',
                                'resultedTestNameTwo',
                                'resultedTestCodeTwo',
                                'resultedTestTwoCodingSystem',
                                'resultedTestResultTwo',
                                'orderingProvider',
                                'orderingProviderStreet',
                                'orderingProviderCity',
                                'orderingProviderState',
                                'orderingProviderZip',
                                'orderingFacilityID',
                                'orderingFacilityDescription',
                                'orderingFacilityStreet',
                                'orderingFacilityCity',
                                'orderingFacilityState',
                                'orderingFacilityZip',
                                'testingFacilityID',
                                'testingFacilityDescription',
                                'testingFacilityStreet',
                                'testingFacilityCity',
                                'testingFacilityState',
                                'testingFacilityZip']

AK_EXPORT_DEFAULTS: Json = {'redacted':'redacted'}

CAMAI_TO_AK_EXPORT_FIELDS: Json = {'patient_id': 'accessionNumber',
                                   'city': 'city',
                                   'dob': 'dateOfBirth',
                                   'race_ethnicity': 'race',
                                   'first_name': 'firstName',
                                   'last_name': 'lastName',
                                   'phone': 'patientPhone',  # Derived field!
                                   'gender': 'patientSex',
                                   'test_performed_datetime': 'specimenAnalysisDate',
                                   'lab_slip_collection_datetime': 'specimenCollectionDate',
                                   'state': 'state',
                                   'street': 'street',
                                   'zip': 'zip'}

if __name__ == '__main__':
    print(APP_ROOT)
