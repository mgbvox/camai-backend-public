from typing import Optional
from pydantic import BaseModel, Field

class UploaderSchema(BaseModel):
    #Options: results, lab
    file_type: str = Field(...)

    class Config:
        schema_extra = {
            "example": {
                "file_type": "results",
            }
        }