from typing import Optional, List
from pydantic import BaseModel, Field
from faker import Faker
import json


class FakeAddress:
    def __init__(self):
        fake = Faker()
        self.street = fake.street_address()
        self.city = fake.city()
        self.state = fake.state()
        self.zip = fake.zipcode()

    def json(self):
        return json.loads(json.dumps(vars(self)))


class Address(BaseModel):
    street: Optional[str] = Field(None)
    city: Optional[str] = Field(None)
    state: Optional[str] = Field(None)
    zip: Optional[str] = Field(None)

    class Config:
        schema_extra = {
            "example": vars(FakeAddress())
        }
