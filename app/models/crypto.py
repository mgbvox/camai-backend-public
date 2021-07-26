from pydantic import BaseModel

class MasterKeyString(BaseModel):
    key_data: str