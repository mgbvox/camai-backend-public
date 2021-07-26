from typing import Any, Dict, List, Optional, Union
from apteryx.utils.http import networking as net

from pydantic import (
    AnyHttpUrl,
    BaseSettings,
    validator,
)


# https://fastapi.tiangolo.com/advanced/settings/


class Settings(BaseSettings):
    '''
    NOTE: This reads from environment variables set in the
    docker-compose environment params for each service. Set
    them there and in the global .env.backend file, not in a .env.backend file
    at this service-level directory root.
    '''
    BACKEND_PROJECT_NAME: str = 'camai-backend'
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    MONGO_USERNAME: str
    MONGO_PASSWORD: str
    MONGO_DATABASE: str = 'main'
    MONGO_URI: str
    KEY_HASH: str

    SIGNALWIRE_DOMAIN: str
    SIGNALWIRE_ACCESS_TOKEN: str
    SIGNALWIRE_PROJECT_ID: str
    SIGNALWIRE_PHONE_NUMBER: str
    NOTIFICATION_PHONE_NUMBERS: List[str]

    class Config:
        case_sensitive = True


settings = Settings()
