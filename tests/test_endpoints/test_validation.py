from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_validate_master_key(master_key_string):
    response = client.post('/validation/', json={
        'key_data': master_key_string
    })
    assert response.status_code == 200
    assert response.json() == True
