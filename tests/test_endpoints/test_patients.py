from fastapi.testclient import TestClient

from app.core.types import Json
from app.main import app
from app.models.patient.patient import RandomPatient, PatientSchema
from app.routes.patient import add_patient_data, update_patient_data, delete_patient_data

client = TestClient(app)


def add_fake_pat(mk: str, override_data: Json = None):
    random_pat = RandomPatient(n_tests=1).json()
    in_pat = PatientSchema(**random_pat)
    if override_data:
        for k in override_data:
            if random_pat.get(k):
                setattr(in_pat, k, override_data[k])


    resp = client.post('/patients/',
                       json={
                           'patient': in_pat.dict(),
                           'master_key_string': {
                               'key_data': mk
                           }
                       })

    data = resp.json()['data']
    pat = data[0][0]['patient_data']
    out_pat = PatientSchema(**pat)
    return in_pat, out_pat, resp


def rm_pat(pid: str, mk: str):
    resp = client.delete(f'/patients/{pid}',
                         json={
                             'key_data': mk
                         })
    return resp


def test_add_and_delete_patient(master_key_string):
    in_pat, out_pat, resp = add_fake_pat(mk=master_key_string)
    assert resp.status_code == 200
    data = resp.json()
    assert 'data' in data
    assert in_pat.dict() == out_pat.dict()

    resp = rm_pat(out_pat.patient_id, mk=master_key_string)
    assert resp.status_code == 200
    message = resp.json()['data'][0]
    assert message == f"Patient with ID: {out_pat.patient_id} removed"


def test_add_patient_with_redundant_pid(master_key_string):
    first_pat, _, _ =  add_fake_pat(master_key_string)
    #Add a second patient with an identical pid
    second_pat, _, resp = add_fake_pat(master_key_string, override_data={
        'patient_id': first_pat.patient_id
    })

    #Somewhere in the insertion the overwritten PID is set to normal again.

    data = resp.json()['data'][0][0]
    assert data['pid_altered'] == True
    assert data['patient_id'] == first_pat.patient_id + '_1'

    rm_pat(first_pat.patient_id, master_key_string)
    rm_pat(data['patient_id'], master_key_string)
