import regex as re
import phonenumbers
from app.core.globals import CODE_TO_NAME


def handle_phone_number(pn_raw):
    if pn_raw:
        pn_raw = str(pn_raw)  # cast to string if not already

        try:
            pn = phonenumbers.format_number(
                phonenumbers.parse(pn_raw),
                phonenumbers.PhoneNumberFormat.INTERNATIONAL
            )
            return pn
        except:
            try:
                pn_raw = '+1' + pn_raw
                pn = phonenumbers.format_number(
                    phonenumbers.parse(pn_raw),
                    phonenumbers.PhoneNumberFormat.INTERNATIONAL
                )
                return pn
            except:
                return pn_raw


def handle_fishery_id(pid: str) -> str:
    match = re.match(r'(\d+)[A-Za-z]+', pid.upper())
    if match:
        _id = str(match.group(1))
        return _id
    else:
        return '33'


def handle_missing_fishery_name(fields: dict) -> str:
    if 'patient_id' in fields:
        fid = handle_fishery_id(fields['patient_id'])
        if fid:
            return CODE_TO_NAME[str(fid.upper())]

    return CODE_TO_NAME['33']
