from typing import Union, List, Any
import asyncio
import os
import base64
import dill as pickle

import cryptography
from cryptography.fernet import Fernet
import hashlib

from app.core.config import settings

from app.core.types import Json


def hash_string(s: str) -> str:
    return str(hashlib.sha3_512(s.encode('utf8')).hexdigest())


def decode_base64_string(enc_string: str) -> bytes:
    return base64.b64decode(enc_string.encode('utf8'))


DO_NOT_ENCRYPT = {
    'fishery_id',
    'fishery_name',
    'pid_hash',
    'base_email_hash'
}


def encrypt(value: Any, key: bytes):
    if value:
        # pickle to bytestring
        pickled = pickle.dumps(value)
        # make cipher
        cipher_suite = Fernet(key)
        # encrypt
        cipher_text = cipher_suite.encrypt(pickled)
        return cipher_text

    else:
        return None


def decrypt(encrypted: Any, key: bytes):
    if encrypted:
        try:
            # Only decrypt bytes objects
            if isinstance(encrypted, bytes):
                cipher_suite = Fernet(key)
                decrypted_bytes = cipher_suite.decrypt(encrypted)
                decrypted_object = pickle.loads(decrypted_bytes)
                return decrypted_object
            else:
                # Otherwise, 'encrypted' is likely already unencrypted
                return encrypted
        except:
            return 'INVALID KEY'
    else:
        return None


def encrypt_object(object_data: Json,
                   master_key: bytes) -> Json:
    if isinstance(object_data, dict):
        encrypted_data = {}
        for k, v in object_data.items():
            if k in DO_NOT_ENCRYPT:
                encrypted_data[k] = v
            else:
                encrypted_data[k] = encrypt_object(v, master_key=master_key)
        return encrypted_data
    if isinstance(object_data, list):
        return [encrypt_object(i, master_key=master_key) for i in object_data]
    else:
        return encrypt(object_data, key=master_key)


def decrypt_object(object_data: Json,
                   master_key: bytes) -> Json:
    if isinstance(object_data, dict):
        decrypted_data = {}
        for k, v in object_data.items():
            if k in DO_NOT_ENCRYPT:
                decrypted_data[k] = v
            else:
                decrypted_data[k] = decrypt_object(v, master_key=master_key)
        return decrypted_data
    if isinstance(object_data, list):
        return [decrypt_object(i, master_key=master_key) for i in object_data]
    else:
        return decrypt(object_data, key=master_key)


async def validate_key(key_data: str):
    target = settings.KEY_HASH
    key_hash = hash_string(key_data)
    return target == key_hash
