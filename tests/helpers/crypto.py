from app.database.crypto import encrypt_object, decrypt_object


def encrypt_decrypt(obj, master_key):
    enc = encrypt_object(obj, master_key)
    dec = decrypt_object(enc, master_key)
    return enc, dec
