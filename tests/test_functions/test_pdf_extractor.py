import pytest
from pydantic import ValidationError

from app.utils.pdfs import pdf_extractor

import tests
from app.utils.pdfs.pdf_extractor import process_lab_file
import asyncio


def test_path_works_instead_of_bytes(lab_form_path):
    assert pdf_extractor.PDFExtractor(lab_form_path).extract_patient() is not None


def test_can_get_pdf_file_name(lab_form_path):
    e = pdf_extractor.PDFExtractor(lab_form_path)
    assert e.name == lab_form_path.name


def test_get_key_exists(lab_form_obj_from_path):
    if not lab_form_obj_from_path.name == 'no_fishery_selected':
        val = lab_form_obj_from_path['fishery_name']['/V']
        assert val
        assert isinstance(val, str)
        assert len(val) > 1


def test_get_key_not_exists(lab_form_obj_from_path):
    assert lab_form_obj_from_path['i_do_not_exist'] == {None: None}


def test_get_key_of_nonexistent_key(lab_form_obj_from_path):
    assert lab_form_obj_from_path['i_do_not_exist'].get('/V') == None


@pytest.mark.asyncio
async def test_extract_patients(lab_form_path):
    e = pdf_extractor.PDFExtractor(lab_form_path)

    async def proc(path):
        result = await process_lab_file(path, process_mode='pdf')
        return result

    should_complete = [i + '.pdf' for i in [
        'good',
        'missing_pid',  # pid is inferred anyway
        'no_fishery_selected',  # fishery should be inferred
        'malformed_dob'
        # parser should be able to handle these malformed types, provided they make sense linguistically

    ]]

    if e.name in should_complete:
        processed = await proc(lab_form_path)
        assert isinstance(processed, dict)

    else:
        with pytest.raises(ValidationError):
            await proc(lab_form_path)
