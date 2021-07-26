from datetime import datetime
from dateparser import parse

# ONLY MAP FIELDS THAT AREN'T IDENTICAL!
KNOWN_OLD_LAB_SLIP_FIELD_MAPPINGS = {'Result': 'positive',
                                     'LastName': 'last_name',
                                     'First Name': 'first_name',
                                     'Month': 'collection_month',
                                     'Day': 'collection_day',
                                     'Year': 'collection_year',
                                     'Month1': 'dob_month',
                                     'Day1': 'dob_day',
                                     'Year1': 'dob_year',
                                     'Text12': 'gender',
                                     'Patient ID Office ONLY': 'patient_id'}

patient_pdf_to_schema = {
    'email': 'email_address',
}

address_pdf_to_schema = {
    'street_physical_address': 'street',
    'city_physical_address': 'city',
    'state_physical_address': 'state',
    'zip_physical_address': 'zip'
}


def make_date(month, day, year):
    try:
        parsed = parse(f'{month} {day} {year}')
        return parsed
    except:
        return


def make_test_datetime(month, day, year, time):
    return {'lab_slip_collection_datetime': None}
