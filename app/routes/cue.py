import base64

import pandas as pd
from app.models.crypto import MasterKeyString
from fastapi import Security, Depends, HTTPException, File, UploadFile, Body
from fastapi.routing import APIRouter
from fastapi.security.api_key import APIKeyQuery, APIKeyHeader, APIKey
from starlette.status import HTTP_403_FORBIDDEN

from app.core.security import KEY_HASHES
from app.database.crypto import hash_string
from app.models.cue import CueResult
from app.routes.patient import get_patients, insert_test_result
from app.utils.csvs.cue_uploads import to_excel_bytes

router = APIRouter()

API_KEY_HASH = KEY_HASHES['cue']
API_KEY_NAME = "access_token"
# COOKIE_DOMAIN = "localtest.me"

api_key_query = APIKeyQuery(name=API_KEY_NAME, auto_error=False)
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)


# api_key_cookie = APIKeyCookie(name=API_KEY_NAME, auto_error=False)

async def validate_api_key(
        api_key_query: str = Security(api_key_query),
        api_key_header: str = Security(api_key_header),
        # api_key_cookie: str = Security(api_key_cookie),
):
    if api_key_query or api_key_header:
        if hash_string(api_key_query) == API_KEY_HASH:
            return api_key_query
        elif hash_string(api_key_header) == API_KEY_HASH:
            return api_key_header
        # elif api_key_cookie == API_KEY:
        #     return api_key_cookie
    else:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN, detail="Could not validate credentials"
        )


@router.post('/reconcile')
async def reconcile_missing_cue_data(master_key_string: str,
                                     # Must be a query param because Body(...) and File(...) aren't compatible.
                                     file: UploadFile = File(...)):
    fbytes = await file.read()
    cue_df = pd.read_excel(fbytes)
    pats = await get_patients(master_key_string)
    pats = pats['data'][0]
    not_in_cue = []
    for p in pats:
        if p['patient_id'] not in cue_df['id'].values:
            not_in_cue.append(p)

    if len(not_in_cue) > 0:
        out_bytes = to_excel_bytes(not_in_cue)
        encoded = base64.b64encode(out_bytes)
        return encoded


@router.post('/test_result')
async def handle_cue_test_result(api_key: APIKey = Depends(validate_api_key),
                                 cue_data: CueResult = Body(...)
                                 ):
    as_test = cue_data.to_test()
    res = await insert_test_result(
        patient_id=cue_data.patient_id,
        test_result=as_test,
        master_key_string=MasterKeyString(key_data=str(api_key))
    )

    return res
