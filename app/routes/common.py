import hashlib
from tqdm import tqdm
from app.database.crypto import decode_base64_string, encrypt_object, decrypt_object



def encrypt_patient_data(patient_data: dict,
                         key_data: str):
    master_key = decode_base64_string(key_data)
    encrypted_patient_data = encrypt_object(patient_data, master_key=master_key)
    return encrypted_patient_data


def decrypt_patient_data(encrypted_patient_data: dict,
                         key_data: str):
    master_key = decode_base64_string(key_data)
    decrypted_patient_data = decrypt_object(object_data=encrypted_patient_data,
                                            master_key=master_key)
    return decrypted_patient_data


def decrypt_multiple_patients(patients: list, key_data: str):
    return [decrypt_patient_data(patient, key_data) for patient in patients]
