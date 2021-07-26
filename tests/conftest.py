import dotenv

dotenv.load_dotenv('../../.env.backend')

from pytest import fixture
from pathlib import Path
from copy import deepcopy

import os
import sys
import asyncio

from app.utils.pdfs.pdf_extractor import PDFExtractor

sys.path.append(os.path.join(os.path.dirname(__file__), 'helpers'))

ROOT = Path(os.path.realpath(__file__)).parent


@fixture(params=[p for p in os.listdir(ROOT / 'datafiles' / 'lab_forms')])
def lab_form_path(request):
    return ROOT / f'datafiles/lab_forms/{request.param}'

@fixture
def lab_form_bytes(lab_form_path):
    with open(lab_form_path, 'rb') as f:
        return deepcopy(f.read())

@fixture
def lab_form_obj_from_path(lab_form_path):
    return PDFExtractor(lab_form_path)

@fixture
def lab_form_obj_from_bytes(lab_form_bytes):
    return PDFExtractor(lab_form_bytes)

@fixture
def master_key():
    return b'REDACTED'


@fixture
def master_key_string():
    return 'REDACTED'


@fixture
def string_for_crypto():
    return 'Hello - I am a string, and you must encrypt me.'


@fixture
def list_for_crypto():
    return ['I am a string', b'I am a byte string', 12345]


@fixture
def json_for_crypto():
    return {
        'a': 'hello',
        'no': 1234,
        'obj_list': [{'1': 'one', '2': 2}, {'3': 'three', '4': 4}],
        'nested': {
            'hi': 'hello',
            'very': {
                'nested': {
                    'object': 'hi',
                    'list': [{'very': {
                        'nested': {
                            'object': 'hi',
                            'list': [1, 2, 3, 4]
                        }
                    }
                    },
                        {'very': {
                            'nested': {
                                'object': 'hi',
                                'list': ['1', '2', '3', '4']
                            }
                        }
                        }
                    ]
                }
            }
        }
    }
