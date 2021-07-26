import numpy as np
import pytz
from typing import Optional, List, Tuple

from fastapi import APIRouter, Body, UploadFile, File
from datetime import timedelta, datetime
import arrow

from app.database.patient import (
    add_patient,
    retrieve_patient,
    retrieve_patients,
    delete_patient,
    update_patient,
    query_db, ensure_pid_unique
)

from app.database.crypto import (
    hash_string,
    decode_base64_string,
    encrypt_object,
    decrypt_object,
    validate_key
)

from app.models.crypto import MasterKeyString

from app.models.patient.patient import (
    PatientSchema,
    ResponseModel,
    ErrorResponseModel,
    RandomPatient
)

from app.models.patient.test_results import Test
from app.routes.common import (
    encrypt_patient_data,
    decrypt_patient_data,
    decrypt_multiple_patients
)

from app.core.types import Json

router = APIRouter()


@router.post('/', response_description='Patient data added to the DB!')
async def add_patient_data(patient: PatientSchema = Body(...),
                           master_key_string: MasterKeyString = Body(...)
                           ):
    valid = await validate_key(master_key_string.key_data)
    if valid:
        patient_data = patient.dict()
        # Make sure a pid_hash is included for searchability!
        patient_id, pid_hash, pid_altered = await ensure_pid_unique(patient_data)

        patient_data['patient_id'] = patient_id
        patient_data['pid_hash'] = pid_hash

        encrypted_patient = encrypt_patient_data(patient_data=patient_data,
                                                 key_data=master_key_string.key_data)

        _ = await add_patient(encrypted_patient)
        return ResponseModel(data=[{'patient_data': patient_data,
                                    'pid_altered': pid_altered,
                                    'pid': patient_id}],
                             message=f'Patient {patient_data["first_name"]} added successfully!')
    else:
        return ErrorResponseModel(error='Invalid Master Key', code=400, message='Your key was invalid.')


@router.get('', response_description='Patients retrieved!')
@router.get('/', response_description='Patients retrieved!')
async def get_patients(master_key_string: str = ""):
    valid = await validate_key(master_key_string)
    if valid:
        encrypted_patients = await retrieve_patients()
        if encrypted_patients:
            patients = decrypt_multiple_patients(patients=encrypted_patients,
                                                 key_data=master_key_string)
            return ResponseModel(patients, 'Patient data retrieved successfully')
        return ResponseModel(None, 'Empty list returned.')
    else:
        return ErrorResponseModel(error='Invalid Master Key', code=400, message='Your key was invalid.')


@router.get('/{patient_id}', response_description='Patient data retrieved')
async def get_patient(patient_id, master_key_string: str = ""):
    valid = await validate_key(master_key_string)
    if valid:
        pid_hash = hash_string(patient_id)
        patient = await retrieve_patient(pid_hash)
        if patient:
            patient_decrypted = decrypt_patient_data(encrypted_patient_data=patient, key_data=master_key_string)
            return ResponseModel(patient_decrypted, 'Patient data retrieved sucessfully')
        return ErrorResponseModel('An error occurred', 404, f'Patient does not exist.')
    else:
        return ErrorResponseModel(error='Invalid Master Key', code=400, message='Your key was invalid.')


@router.put('/{patient_id}')
async def update_patient_data(patient_id: str,
                              req: PatientSchema = Body(...),
                              master_key_string: MasterKeyString = Body(...)):
    valid = await validate_key(master_key_string.key_data)
    if valid:
        pid_hash = hash_string(patient_id)
        patient_enc = await retrieve_patient(pid_hash)
        patient_data = decrypt_patient_data(encrypted_patient_data=patient_enc,
                                            key_data=master_key_string.key_data)
        update_data = req.dict()
        for k in update_data:
            patient_data[k] = update_data[k]

        # Re-validate the updated data
        validated_updated = PatientSchema(**patient_data)

        updated_patient_enc = encrypt_patient_data(validated_updated.dict(), key_data=master_key_string.key_data)

        updated_patient = await update_patient(pid_hash, updated_patient_enc)
        if updated_patient:
            return ResponseModel(
                f"Patient with PID: {patient_id} update was successful",
                "Patient updated successfully",
            )
        return ErrorResponseModel(
            "An error occurred",
            404,
            "There was an error updating the patient_data data.",
        )


def handle_incomplete_tests(incomplete_tests, new_test):
    new_test_dt = arrow.get(new_test['test_performed_datetime']).astimezone(pytz.utc)
    best_match = None
    best_match_idx = None
    best_distance = np.inf
    '''
    Find the existing, incomplete test which is 
    1) closest to the current cue result administration date, and 
    2) not in the future, OR - if it is: 
        2b) within the window of error for human error in time reporting (here, three days)
    '''
    for idx, t in incomplete_tests:
        if t.get('lab_slip_collection_datetime'):
            lab_dt = arrow.get(t['lab_slip_collection_datetime']).astimezone(pytz.utc)
            delta = (new_test_dt - lab_dt).total_seconds()
            three_days_in_seconds = 60 * 60 * 24 * 3
            if (delta < best_distance) and ((delta > 0) or (abs(delta) < three_days_in_seconds)):
                best_match_idx = idx
                best_match = t
                best_distance = delta
    return best_match_idx, best_match


@router.put("/{patient_id}/test_result")
async def insert_test_result(patient_id: str,
                             master_key_string: MasterKeyString = Body(...),
                             test_result: Test = Body(...)):
    valid = await validate_key(master_key_string.key_data)
    if valid:
        pid_hash = hash_string(patient_id.upper())

        patient_enc = await retrieve_patient(pid_hash)

        if not patient_enc:
            return ErrorResponseModel(error='Patient not found.',
                                      code=400,
                                      message=f'Patient with PID {patient_id} not found in our database.')

        patient_data = decrypt_patient_data(encrypted_patient_data=patient_enc,
                                            key_data=master_key_string.key_data)

        # Find incomplete (e.g. lab slip data only) test results.
        patient_tests = patient_data['test_results']

        # Make sure this test hasn't already been logged
        for pt in patient_tests:
            if test_result.test_id == pt['test_id']:
                return ErrorResponseModel(
                    error='This test result already uploaded!',
                    code=400,
                    message=f'Test with test_id {test_result.test_id} already exists in our system.'
                )

        incomplete_tests = [(test_idx, t) for test_idx, t in enumerate(patient_tests) if not t.get('test_id')]
        if not incomplete_tests or len(incomplete_tests) < 1:
            return ErrorResponseModel(error='No Corresponding Lab Slip', code=400,
                                      message=f'There are no incomplete tests for this patient (PID: {patient_id}). Likely you need to upload their Lab Order Form PDF first.')

        new_test_dict = test_result.dict()
        if not new_test_dict['test_reported_datetime']:
            new_test_dict['test_reported_datetime'] = datetime.now().isoformat()
        test_idx, test_to_update = handle_incomplete_tests(incomplete_tests, new_test_dict)
        if isinstance(test_idx, int) and isinstance(test_to_update, dict):
            for k in ['test_id', 'test_performed_datetime', 'test_reported_datetime', 'positive']:
                test_to_update[k] = new_test_dict[k]
            patient_tests[test_idx] = test_to_update
            patient_data['test_results'] = patient_tests
            patient_enc = encrypt_patient_data(patient_data, key_data=master_key_string.key_data)

            updated_patient = await update_patient(pid_hash, patient_enc)
            if updated_patient:
                return ResponseModel(
                    f"Patient with PID: {patient_id} update was successful",
                    "Patient updated successfully", )
            else:
                return ErrorResponseModel(
                    error='Unable to update patient',
                    code=400,
                    message=f'Unable to update patient with PID {patient_id}'
                )
        else:
            return ErrorResponseModel(
                error='Not able to add result to patient tests',
                code=400,
                message=f'''
Patient with PID {patient_id} had incomplete tests,
but the result you are trying to upload could 
not be matched with any of them. Likely this 
is due to 1) a missing lab slip upload, or 
2) a missing lab_slip_completed_datetime field in 
a test that was already uploaded. Please check 
your patient records on the results page.'''.strip().replace('\n', ' ')
            )

    else:
        return ErrorResponseModel(error='Invalid Master Key', code=400, message='Your key was invalid.')


def get_test_by_id(tests: List[Json], test_id: str) -> Tuple[int, Json]:
    for i, t in enumerate(tests):
        if t['test_id'] == test_id:
            return i, t


@router.put("/{patient_id}/test_result/{test_id}")
async def update_test_result(
        patient_id: str,
        test_id: str,
        master_key_string: MasterKeyString = Body(...),
        test_result_updates: Json = Body(...)
):

    if (not test_id) or (len(test_id) == 0):
        return ErrorResponseModel(
            error= 'No Test ID',
            code = 400,
            message = f"Submitted test has no Test ID (patient_id {patient_id}); please make sure to upload CUE results first!"
        )

    valid = await validate_key(master_key_string.key_data)
    if valid:
        pid_hash = hash_string(patient_id)
        patient = await retrieve_patient(pid_hash)
        if patient:
            patient_decrypted = decrypt_patient_data(encrypted_patient_data=patient,
                                                     key_data=master_key_string.key_data)
            test_idx, test_to_update = get_test_by_id(patient_decrypted['test_results'], test_id)
            if test_to_update:
                # For every key in the update, update in the old test.
                for k, v in test_result_updates.items():
                    test_to_update[k] = v
                # Update the test at the correct index
                patient_decrypted['test_results'][test_idx] = test_to_update
                # Encrypt the updated patient
                updated_patient_enc = encrypt_patient_data(patient_decrypted,
                                                           key_data=master_key_string.key_data)

                # Update the encrypted data in Mongo
                updated_patient = await update_patient(pid_hash, updated_patient_enc)
                if updated_patient:
                    return ResponseModel(
                        f"Patient with PID: {patient_id}, TID: {test_id} update was successful",
                        "Patient updated successfully",
                    )
                return ErrorResponseModel(
                    error="Update error",
                    code=404,
                    message=f"There was an error updating the test data for PID: {patient_id}, TID: {test_id}.",
                )

            else:
                return ErrorResponseModel(
                    error='Test ID Not Found',
                    code=400,
                    message=f'Test with Test ID {test_id} not found for patient with PID {patient_id}.'
                )


    else:
        return ErrorResponseModel(error='Invalid Master Key', code=400, message='Your key was invalid.')


@router.delete('/{patient_id}', response_description="Patient data deleted from the database")
async def delete_patient_data(patient_id: str, master_key_string: MasterKeyString = Body(...)):
    valid = await validate_key(master_key_string.key_data)
    if valid:
        pid_hash = hash_string(patient_id)
        deleted_patient = await delete_patient(pid_hash)
        if deleted_patient:
            return ResponseModel(
                f"Patient with ID: {patient_id} removed", "Patient deleted successfully"
            )
        return ErrorResponseModel(
            "An error occurred", 404, f"Patient with id {patient_id} doesn't exist"
        )
    else:
        return ErrorResponseModel(error='Invalid Master Key', code=400, message='Your key was invalid.')


@router.post('/query', response_description='MongoDB query performed on patient database!')
async def do_db_query(query: dict = Body(...),
                      decrypt: bool = Body(...),
                      master_key_string: MasterKeyString = Body(...)):
    valid = await validate_key(master_key_string.key_data)
    if valid:
        query_result = await query_db(query)
        if query_result:
            if decrypt:
                decrypted_query_result = decrypt_multiple_patients(query_result, key_data=master_key_string.key_data)
                return decrypted_query_result
            else:
                return query_result
        else:
            return ErrorResponseModel(
                "An error occurred", 404, f"Unable to perform query."
            )
    else:
        return ErrorResponseModel(error='Invalid Master Key', code=400, message='Your key was invalid.')
