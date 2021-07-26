import os

from fastapi import APIRouter
from app.models.crypto import MasterKeyString
from app.database.crypto import validate_key

router = APIRouter()


@router.post('/')
async def validate_master_key(master_key_string: MasterKeyString):
    '''
    Takes a user-provided master key and checks whether it can successfully decrypt a
    target phrase. If so, returns true; else, false.
    '''

    validation_status = await validate_key(master_key_string.key_data)
    return validation_status
