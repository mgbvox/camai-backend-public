from fastapi.testclient import TestClient
import os

from app.main import app

client = TestClient(app)
