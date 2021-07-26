import regex as re


def lab_text_to_patient_data(text):
    lines = text.split("\n")
    patient_id_next = False
    name_next = False
    patient_data = {}
    for l in lines:
        if l.isspace() or len(l) < 1:
            continue
        if "Patient ID" in l:
            patient_id_next = True
        elif patient_id_next:
            patient_data['patient_id'] = parse_lab_id_line_to_id(l)
            patient_id_next = False
        elif "Last Name" in l:
            name_next = True
        elif name_next:
            patient_data['name'] = parse_lab_name_line_to_name(l)
            name_next = False
    return patient_data


def parse_lab_name_line_to_name(line):
    l = line.split("PO")[0].strip()
    fl_list = re.sub(r'[^a-zA-Z0-9 ]', '', l).split(' ')
    return " ".join(fl_list)


def parse_lab_id_line_to_id(line):
    l = line.split("|")[0].strip().upper()
    return re.sub(r'[^a-zA-Z0-9]', '', l)
