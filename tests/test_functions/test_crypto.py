import pytest
from tests.helpers.crypto import encrypt_decrypt


def test_encrypt_decrypt_STRING(string_for_crypto, master_key):
    enc, dec = encrypt_decrypt(string_for_crypto, master_key)
    assert all([isinstance(enc, bytes), string_for_crypto != enc, string_for_crypto == dec])


def test_encrypt_decrypt_LIST(list_for_crypto, master_key):
    enc, dec = encrypt_decrypt(list_for_crypto, master_key)
    for o, e, d in zip(list_for_crypto, enc, dec):
        assert o != e
        assert e != d
        assert o == d


def test_encrypt_decrypt_JSON(json_for_crypto, master_key):
    enc, dec = encrypt_decrypt(json_for_crypto, master_key)
    assert enc is not None
    assert json_for_crypto == dec


class aThing:
    def __init__(self, val):
        self.val = val

    def fun(self):
        return self.val + 1


def test_encrypt_decrypt_CLASS(master_key):
    obj = aThing(1)
    enc, dec = encrypt_decrypt(obj, master_key)
    assert obj.fun() == 2
    assert dec.fun() == 2
    assert isinstance(enc, bytes)
