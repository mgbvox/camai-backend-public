from app.models.patient.patient import (
    PatientSchema,
    ResponseModel,
    ErrorResponseModel
)
from app.database.patient import (
    retrieve_patient,
    retrieve_patients,
    delete_patient,
    update_patient
)

# from app.processing.text import hl7_processing as hl7

import datetime as dt

from fastapi import APIRouter, Body
from fastapi.encoders import jsonable_encoder
import os
from typing import List
from collections import defaultdict
from app.core.types import Json
from app.models.patient.test_results import TestStrict

script_dir = os.path.dirname(__file__)

router = APIRouter()

@router.post('/malformed_patient_data')
async def malformed_patient_data(pats: List[dict] = Body(...)) -> Json:
    malformed_patients = defaultdict(list)
    for p in pats:
        for t in p['test_results']:
            try:
                _ = TestStrict(**t)
            except:
                malformed_patients[p['patient_id']].append(t)
    malformed_pids = list(malformed_patients.keys())
    return {
        'pids': malformed_pids,
        'pids_to_tests': malformed_patients
    }