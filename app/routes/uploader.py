import base64

from app.models.crypto import MasterKeyString
from fastapi import APIRouter, File, UploadFile, Body
from typing import List
from collections import defaultdict

from app.core.types import Json

from app.models.patient.patient import ErrorResponseModel, ResponseModel

from app.database.crypto import validate_key, hash_string
from app.database.patient import (update_patient, add_patient, retrieve_patient, ensure_pid_unique)

from app.routes.common import (
    encrypt_patient_data,
    decrypt_patient_data,
)

from app.utils.pdfs.pdf_extractor import process_lab_file
from app.utils.images.image_processing import process_image_pdf_to_txt
from app.utils.text.result_text_parsing import scrape_patient_data
from app.utils.sms import alert_sms

from app.utils.csvs.cue_uploads import PATIENT_EXPORT_FIELDS, CUE_IMPORT_FIELDS, get_csv_data_from_pat, to_excel_bytes

router = APIRouter()

FILE_TYPES_AND_PROCESS_MODES = {'lab': ['pdf'],
                                'results': ['pdf', 'ocr', 'cepheid']}


async def search_for_existing_patient(extracted_data):
    retrieved = await retrieve_patient(pid_hash=hash_string(extracted_data['patient_id']))
    return retrieved


@router.post('/{file_type}/{process_mode}', response_description='Patient data added to the DB!')
async def process_pdf(file_type: str,
                      process_mode: str,
                      master_key_string: str,
                      # Must be a query param because Body(...) and File(...) aren't compatible.
                      file: UploadFile = File(...),
                      ):
    type_and_mode_okay = (file_type.lower() in FILE_TYPES_AND_PROCESS_MODES) and (
            process_mode.lower() in FILE_TYPES_AND_PROCESS_MODES[file_type])
    if not type_and_mode_okay:
        return ErrorResponseModel(
            f'Invalid Endpoint',
            400,
            f'/{file_type}/{process_mode} not a valid endpoint. Must be in /[lab|results]/[pdf|ocr|cepheid].\n'
            f' All valid modes: {FILE_TYPES_AND_PROCESS_MODES}'
        )

    valid = await validate_key(master_key_string)
    if valid:
        if file_type == 'results':
            '''
            For results, the only uploads should be scanned AK State results - this should only need OCR.
            CUE data is sent via API endpoint and extracted on the frontend.
            '''
            extracted_data = process_results_file(file, process_mode)
            return extracted_data

            # TODO: update EXISTING test data populated from lab slip.



        elif file_type == 'lab':
            extracted_data = await process_lab_file(file, process_mode)
            if extracted_data:  # do not add a patient if no data was found

                # DO NOT CHANGE THE ORDER OF THESE WITHOUT TELLING CECELIA
                omit = ['email_address', 'home_phone']
                csv_data = []
                csv_data_json = defaultdict(None)

                patent_export_fields_stringified = [str(i) for i in PATIENT_EXPORT_FIELDS]
                pat_to_cue_field_map = dict(zip(patent_export_fields_stringified, CUE_IMPORT_FIELDS))

                for k in PATIENT_EXPORT_FIELDS:
                    # Use str(k) instead of k as key, since k can be a list.
                    json_field = pat_to_cue_field_map[str(k)]
                    if k not in omit:
                        csv_data.append(get_csv_data_from_pat(pat=extracted_data, key=k))
                        csv_data_json[json_field] = get_csv_data_from_pat(pat=extracted_data, key=k)
                    else:
                        csv_data.append(None)
                        csv_data_json[json_field] = None

                # Check to see if patient exists!
                patient_enc = await search_for_existing_patient(extracted_data)
                if patient_enc:
                    # Update with new test data (incomplete) if patient already exists (e.g. this is test #2)
                    patient = decrypt_patient_data(encrypted_patient_data=patient_enc,
                                                   key_data=master_key_string)

                    '''
                    Check all extant test data in patient
                        - if lab_slip_collection_datetime MATCH, don't add (this is a repeat upload)
                    '''
                    new_incomplete_test_data = extracted_data['test_results'][0]
                    new_test_dt = new_incomplete_test_data['lab_slip_collection_datetime']
                    dt_match_found = False
                    for test in patient['test_results']:
                        test_dt = test['lab_slip_collection_datetime']
                        if test_dt == new_test_dt:
                            dt_match_found = True
                    if not dt_match_found:
                        patient['test_results'].append(new_incomplete_test_data)
                        updated_patient_enc = encrypt_patient_data(patient_data=patient,
                                                                   key_data=master_key_string)

                        patient_updated = await update_patient(pid_hash=patient['pid_hash'], data=updated_patient_enc)

                        if patient_updated:
                            return ResponseModel(data={'csv_data': csv_data,
                                                       'patient_json': patient},
                                                 message=f"Patient with pid {extracted_data['patient_id']} had test data successfully added!")
                        else:

                            return ErrorResponseModel(
                                error='Unable to update patient',
                                code=400,
                                message=f"Unable to update patient with PID {extracted_data['patient_id']}"
                            )
                    else:
                        return ErrorResponseModel(
                            error='Unable to update patient',
                            code=400,
                            message=f"This lab slip was already uploaded (patient {patient['patient_id']}, tested at {new_test_dt})."
                        )
                else:
                    # Create a new patient record

                    # Ensure the PID is unique!
                    patient_id, pid_hash, pid_altered = await ensure_pid_unique(extracted_data)
                    extracted_data['patient_id'] = patient_id
                    extracted_data['pid_hash'] = pid_hash

                    # Drop all none patient fields

                    extracted_data = {k: v for k, v in extracted_data.items() if v is not None}

                    patient_enc = encrypt_patient_data(patient_data=extracted_data, key_data=master_key_string)

                    patient_added = await add_patient(patient_enc)

                    if patient_added:
                        return ResponseModel(data={'patient': extracted_data,
                                                   'pid_altered': pid_altered,
                                                   'pid': patient_id,
                                                   'patient_json': extracted_data,
                                                   },
                                             message=f"Patient with pid {extracted_data['patient_id']} added to database!")
                    else:
                        ErrorResponseModel(
                            error='Unable to add patient',
                            code=400,
                            message=f"Unable to add patient with PID {extracted_data['patient_id']} to database."
                        )
            else:
                return ErrorResponseModel(error='An error occurred',
                                          code=404,
                                          message=f'Patient data could not be extracted from lab file.')
        else:
            return ErrorResponseModel(error='An error occurred',
                                      code=404,
                                      message=f'file_type must be either results or lab.'
                                      )

        return ErrorResponseModel(error='Unexpected Code Executed', code=400,
                                  message='You reached a point in code that should not be reachable.')
    else:
        return ErrorResponseModel(error='Invalid Master Key', code=400, message='Your key was invalid.')



def process_results_file(file_bytes, process_mode):
    '''
    NOTE: Will need to check OCR extracted pid against extant patient pids - correct for translation noise.
    '''
    if process_mode == 'ocr':
        txt = process_image_pdf_to_txt(file_bytes)
        data = scrape_patient_data(txt)
        return data
    else:
        pass
