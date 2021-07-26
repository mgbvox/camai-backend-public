import pathlib
from typing import Iterable, Dict, Any, Union
import PyPDF2 as pypdf
import io

from starlette.datastructures import UploadFile
from pydantic import ValidationError

from app.utils.sms import alert_sms
from app.utils.db import check_email_address
from app.utils.pdfs.field_mappings import (make_date, patient_pdf_to_schema,
                                           address_pdf_to_schema, KNOWN_OLD_LAB_SLIP_FIELD_MAPPINGS)
from app.utils.pdfs.extractor_utils import handle_missing_fishery_name, handle_phone_number
from app.core.globals import NAME_TO_CODE, CODE_TO_NAME
from app.models.patient.patient import PatientSchema
from app.models.patient.test_results import Test
from app.models.patient.address import Address
from app.database.crypto import hash_string


def apply_field_map(d, fmap):
    return {fmap.get(k, k): v for k, v in d.items()}


class PDFExtractor:
    def __init__(self, pdf_file: Union[UploadFile, bytes, str, pathlib.Path]):
        if isinstance(pdf_file, UploadFile):
            self.name = pdf_file.filename
            self.pdf = pypdf.PdfFileReader(pdf_file)
        elif isinstance(pdf_file, bytes):
            iostream = io.BytesIO(pdf_file)
            iostream.seek(0)
            self.pdf = pypdf.PdfFileReader(iostream)
        elif isinstance(pdf_file, (str, pathlib.Path)):
            self.name = pathlib.Path(pdf_file).name
            self.pdf = pypdf.PdfFileReader(open(pdf_file, 'rb'))
        else:
            raise ValueError(
                f'pdf_file is the wrong type (provided {type(pdf_file)}; expected Union[bytes, str, pathlib.Path])')
        # map fields to standard extractor fields
        self.fields = apply_field_map(self.pdf.getFields(), KNOWN_OLD_LAB_SLIP_FIELD_MAPPINGS)

    def __getitem__(self, key):
        return self.fields.get(key, {None: None})

    def search(self, s):
        return [k for k in self.fields.keys() if s.upper() in k.upper()]

    def extract(self, fields=Iterable[str]) -> Dict[str, Any]:
        return {k: self[k].get('/V').strip() if self[k].get('/V') else None for k in fields}

    def handle_caps(self, data):
        leave = ['email_address']
        return {k: v.upper() if (v not in leave and v) else v for k, v in data.items()}

    def extract_patient(self):
        data = self.extract(
            fields=['first_name', 'last_name', 'patient_id', 'ssn', 'gender', 'race_ethnicity', 'hispanic',
                    'home_phone', 'cell_phone', 'local_phone', 'email_address',
                    'fishery_name', 'insurance', 'been_here_before'])

        fields_mapped = self.handle_caps(apply_field_map(data, patient_pdf_to_schema))

        if 'fishery_name' not in fields_mapped or fields_mapped['fishery_name'] == '---':
            fields_mapped['fishery_name'] = handle_missing_fishery_name(fields_mapped)

        for k in fields_mapped.keys():
            if 'phone' in k.lower():
                fields_mapped[k] = handle_phone_number(fields_mapped[k])

        # Process and clean data
        # Make patient_id case insensitive (all upper)
        fields_mapped['patient_id'] = fields_mapped['patient_id'].upper()
        fields_mapped['email_address'] = fields_mapped['email_address'].lower() if fields_mapped[
            'email_address'] else 'noemail@nowhere.com'

        # Get fishery code
        fishery_name = fields_mapped.get('fishery_name')
        if fishery_name:
            fields_mapped['fishery_id'] = NAME_TO_CODE.get(fishery_name.upper())
        else:
            pid = fields_mapped.get('patient_id')
            if pid:
                fid = pid[:2]
                if fid.replace('0', '').isdigit():
                    fields_mapped['fishery_id'] = fid
                    fields_mapped['fishery_name'] = CODE_TO_NAME[fid]


        dob_data = self.extract(fields=['dob_month', 'dob_day', 'dob_year'])
        if dob_data:
            dob = make_date(dob_data['dob_month'], dob_data['dob_day'], dob_data['dob_year'])
            if dob:
                fields_mapped['dob'] = dob.isoformat()
        else:
            pid = fields_mapped.get('patient_id')
            if pid:
                m = pid[-8:-6]
                d = pid[-6:-4]
                y = pid[-4:]
                dob = make_date(m,d,y)
                if dob:
                    fields_mapped['dob'] = dob.isoformat()


        return fields_mapped

    def extract_address(self):
        data = self.extract(fields=[
            'street', 'city', 'state', 'zip'
        ])
        fields_mapped = apply_field_map(data, address_pdf_to_schema)
        address_object = Address(**fields_mapped)

        return address_object

    def extract_test(self):
        data = self.extract(fields=[
            'collection_month', 'collection_day', 'collection_year'
        ])

        slip_date = make_date(data['collection_month'], data['collection_day'],
                              data['collection_year'])

        test_data = {
            'specimen_type': 'NP-Nasopharyngeal swab',
            'lab_slip_collection_datetime': slip_date.isoformat() if slip_date else None
        }

        test_obj = [Test(**test_data)]

        return test_obj


async def lab_slip_db_checks(extracted_data):
    if 'base_email_hash' in extracted_data:
        # Hash email for searchability
        extracted_data['base_email_hash'] = hash_string(extracted_data['email_address'])
        # Find other matching hashes and increment this email by that many plus one.
        extracted_data['email_address'] = await check_email_address(extracted_data['email_address'])

        return extracted_data


async def process_lab_file(file_bytes: Union[bytes, str, UploadFile],
                           process_mode: str,
                           do_checks: bool = True) -> Union[dict, None]:
    file_name = None
    if isinstance(file_bytes, UploadFile):
        file_name = file_bytes.filename
        file_bytes = await file_bytes.read()
    if process_mode == 'pdf':
        try:
            e = PDFExtractor(file_bytes)
            patient_data = e.extract_patient()
            address_data = e.extract_address()
            patient_data['physical_address'] = address_data
            test_data = e.extract_test()
            patient_data['test_results'] = test_data
        except:
            msg = f'File {file_name if file_name else ""} could not be parsed by PDFExtractor.'
            await alert_sms(body=msg)
            return {'NOT_IMPLEMENTED': 'NO'}
        try:
            validated = PatientSchema(**patient_data).dict()
            if do_checks:
                checked = await lab_slip_db_checks(validated)
                return checked
            return validated
        except ValidationError as e:
            msg = f'File {file_name if file_name else ""} had missing fields:'
            missing = '\n'.join([f"{err['type']}: {err['loc'][0]}" for err in e.errors()])
            msg += '\n' + missing
            await alert_sms(body=msg)

        return None

    else:
        # If OCR ever implemented for Lab forms, implement this.
        return None
