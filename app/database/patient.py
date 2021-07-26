from typing import Union
from app.database.crypto import hash_string
from app.core.config import settings
from app.routes.common import decrypt_patient_data


async def get_patient_collection():
    from app.main import MONGO_CLIENT
    database = MONGO_CLIENT.get_database(settings.MONGO_DATABASE)
    collection = database.get_collection("patients")

    return MONGO_CLIENT, database, collection


def patient_helper(patient_data: dict) -> dict:
    patient_data['_id'] = str(patient_data['_id'])
    return patient_data


async def ensure_pid_unique(patient_data: dict):
    '''
    Make sure pid_hash isn't already in db
    If so:
        append ints to the end of pid until pid_hash is unique.
    '''

    pid = patient_data['patient_id']

    increment = 0
    pid_hash = hash_string(pid)
    pid_exists = bool(await retrieve_patient(pid_hash))
    pid_altered = False
    while pid_exists:
        pid_altered = True
        increment += 1
        incremented_pid = f'{pid}_{increment}'
        pid = incremented_pid
        pid_hash = hash_string(pid)
        pid_exists = bool(await retrieve_patient(pid_hash))
    return pid, pid_hash, pid_altered



async def add_patient(patient_data: dict) -> dict:
    _, _, collection = await get_patient_collection()
    patient = await collection.insert_one(patient_data)
    new_patient = await collection.find_one({'_id': patient.inserted_id})
    return patient_helper(new_patient)


async def retrieve_patients(query={}):
    _, _, collection = await get_patient_collection()
    patients = []
    async for patient in collection.find(query):
        patients.append(patient_helper(patient))
    return patients


async def retrieve_patient(pid_hash: str) -> Union[dict, None]:
    _, _, collection = await get_patient_collection()
    try:
        patient = await collection.find_one({'pid_hash': pid_hash})
        return patient_helper(patient)
    except:
        cursor = collection.find({'pid_hash': pid_hash})
        patients = await cursor.to_list(length=1)
        if len(patients) > 0:
            return patient_helper(patients[0])
    return None


async def update_patient(pid_hash: str, data: dict) -> Union[bool, dict]:
    _, _, collection = await get_patient_collection()
    if len(data) < 1:
        return False
    patient = await collection.find_one({'pid_hash': pid_hash})

    if patient:
        # Remove _id since it should never be updated.
        if '_id' in data:
            _ = data.pop('_id')
        updated_patient = await collection.update_one(
            {'pid_hash': pid_hash}, {'$set': data}
        )
        if updated_patient:
            return updated_patient.raw_result
        return False


async def delete_patient(pid_hash: str):
    _, _, collection = await get_patient_collection()
    patient = await collection.find_one({'pid_hash': pid_hash})
    if patient:
        await collection.delete_one({'pid_hash': pid_hash})
        return True


async def query_db(query: dict) -> Union[None, list]:
    _, _, collection = await get_patient_collection()
    patients = []
    async for patient in collection.find(query):
        patients.append(patient_helper(patient))
    if patients:
        return patients
