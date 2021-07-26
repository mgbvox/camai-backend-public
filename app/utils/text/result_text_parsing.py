import regex as re

def find_name(text):
    name_matches = re.findall(r'NAME\s(.*?\,\s.*?)\s', text)
    if not name_matches:
        return ("", "")
    if len(name_matches) > 1:
        print('MULTIPLE NAMES FOUND!')
        print(name_matches)
    last, first = [part.strip() for part in name_matches[0].split(',')]
    return (last, first)


def find_dob(text):
    date_matches = re.findall(r'\d{1,2}/\d{1,2}/\d{4}', text)
    if date_matches:
        mm, dd, yyyy = date_matches[0].split('/')
        return mm, dd, yyyy


def find_patient_id(text, first, last):
    pattern = r'\d{1,2}' + f'{last[:3]}{first[:3]}' + r'\d{6,8}'
    print(pattern)
    matches = re.findall(pattern, text)
    print(matches)
    if not matches:
        print("NO MATCH FOUND")
        return ""
    if len(matches) > 1:
        print('MULTIPLE IDS FOUND!')
        print(matches)
    return matches[0]


def scrape_patient_data(text):
    #UPPERCASE for ease of search.
    text = text.upper()
    last, first = find_name(text)
    mm, dd, yyyy = find_dob(text)
    patient_id = find_patient_id(text, first, last)
    if f'{mm}{dd}{yyyy}' not in patient_id:
        print(f'WARNING: dob does not align with patient_id:\nDOB: {mm}{dd}{yyyy}\nPID: {patient_id}')
    return {
        'name': f'{first} {last}',
        'patient_id': patient_id,
        'positivity': 'positive'
    }