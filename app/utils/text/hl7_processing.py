import hl7


def parse_result(message):
    h = hl7.parse(message)
    pid = h.segments('PID')[0]
    patient_id = pid[2][0]
    patient_name = pid[5][0]
    patient_dob = pid[7]
    patient_sex = pid[8]
    patient_addr = pid[11]
    patient_result = h.segments('OBX')[0][5]
    collection_type = h.segments('SPM')[0][4]
    specimen_collection_datetime = h.segments('OBX')[0][14]
    return {
        'patient_id': patient_id, 
        'name': patient_name[1][0] + " " + patient_name[0][0], 
        'dob': patient_dob, 
        'gender': patient_sex, 
        'address': patient_addr,
        'positivity': patient_result[0][1],
        'collection_type': collection_type[0][1],
        'specimen_collection_datetime': specimen_collection_datetime
    }

