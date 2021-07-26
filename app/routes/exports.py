from datetime import datetime

import base64
from typing import List, Optional

import pandas as pd
from fastapi import APIRouter, Body

from app.core.globals import CAMAI_TO_AK_EXPORT_FIELDS, AK_EXPORT_DEFAULTS, AK_EXPORT_COLUMNS
from app.core.types import Json
from app.database.crypto import validate_key, DO_NOT_ENCRYPT
from app.database.patient import retrieve_patients
from app.routes.common import decrypt_multiple_patients
from app.models.crypto import MasterKeyString
from app.models.patient.patient import ErrorResponseModel
from app.models.dates import DateRange
from app.utils.csvs.cue_uploads import to_excel_bytes, df_to_bytes
from app.utils.datetimes import to_dt

router = APIRouter()


@router.post('/gen_cue_excel')
async def generate_cue_excel_from_pats(pats: List[Json] = Body(...), master_key_string: MasterKeyString = Body(...)):
    valid = await validate_key(master_key_string.key_data)
    if valid:
        out_bytes = to_excel_bytes(pats)
        encoded = base64.b64encode(out_bytes)
        return {'excel_bytes_base_64': encoded}
    else:
        return ErrorResponseModel(error='Invalid Master Key', code=400, message='Your key was invalid.')


def flatten_pat(p):
    a = p.copy()
    # Remove nested fields:
    a.pop('physical_address')
    a.pop('test_results')

    # Update the main dict with the fields from p
    a.update(p['physical_address'])
    tests = p['test_results']
    flattened_records = []
    for t in tests:
        record = a.copy()
        record.update(t)
        flattened_records.append(record)
    return flattened_records


@router.post('/gen_ak_state_report')
async def generate_ak_state_report(
        query: dict = Body(None, description='Queries to filter the results, if any. Must be equivalence based.'),
        date_range: Optional[DateRange] = Body(None, description="Start and end date as iso strings (UTC encoded)"),
        master_key_string: MasterKeyString = Body(...)):
    valid = await validate_key(master_key_string.key_data)
    if valid:
        mongo_query = {}
        df_query = {}
        if query:
            # Include un-encrypted fields in patient search to speed things up.
            mongo_query = {k: v for k, v in query.items() if k in DO_NOT_ENCRYPT}
            # Other encrypted fields must be filtered after the fact (from the df)
            df_query = {k: v for k, v in query.items() if k not in DO_NOT_ENCRYPT}

        pats_enc = await retrieve_patients(query=mongo_query)
        pats = decrypt_multiple_patients(pats_enc, key_data=master_key_string.key_data)
        records = []
        for p in pats:
            records += flatten_pat(p)
        df = pd.DataFrame.from_records(records)

        if df_query:
            # Filter the df by each key-value pair in the query dict.
            query_string = ' and '.join([f"{k}=='{v}'" for k, v in df_query.items()])
            df = df.query(query_string)

        # Filter dates!
        # Do that here.
        #####
        if date_range:
            df = df[df.lab_slip_collection_datetime.apply(to_dt).between(date_range.start_datetime, date_range.end_datetime)]


        #1) Do any more type conversions/formatting as needed
        #dob to mm/dd/yyyy
        def to_ak_dob(dt: datetime):
            if dt:
                return f"{str(dt.month).zfill(2)}/{str(dt.day).zfill(2)}/{str(dt.year).zfill(4)}"
        df['dob'] = df.dob.apply(to_dt).apply(to_ak_dob)

        def get_ak_phone(r):
            if r.local_phone: return r.local_phone
            if r.cell_phone: return r.cell_phone
            if r.home_phone: return r.home_phone

        df['phone'] = df.apply(get_ak_phone, axis=1)
        df['ethnicity'] = df.race_ethnicity

        # Do field mappings last
        # Do those here
        #####
        export = df[list(CAMAI_TO_AK_EXPORT_FIELDS.keys()) + ['ethnicity']]
        for k, v in AK_EXPORT_DEFAULTS.items():
            export[k] = v
        export.columns = [CAMAI_TO_AK_EXPORT_FIELDS.get(k, k) for k in export.columns]
        export = export[AK_EXPORT_COLUMNS]

        #Sort output by specimenCollectionDate, descending.
        export.sort_values(by='specimenCollectionDate', ascending=False)

        excel_bytes = df_to_bytes(export)
        encoded = base64.b64encode(excel_bytes)
        return {'excel_bytes_base_64': encoded}
    else:
        return ErrorResponseModel(error='Invalid Master Key', code=400, message='Your key was invalid.')
