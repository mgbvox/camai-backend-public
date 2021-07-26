import uvicorn
import dotenv
from app.models.patient.patient import ErrorResponseModel

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import pymongo

from app.core.config import settings

from app.routes.patient import router as PatientRouter
from app.routes.uploader import router as UploadRouter
from app.routes.results import router as ResultsRouter
from app.routes.validation import router as ValidationRouter
from app.routes.cue import router as CueRouter
from app.routes.exports import router as ExportsRouter


def get_application():
    _app = FastAPI(title=settings.BACKEND_PROJECT_NAME)

    _app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return _app


app = get_application()

MONGO_CLIENT = AsyncIOMotorClient(settings.MONGO_URI)

app.include_router(PatientRouter, tags=["Patient"], prefix="/api/patients")
app.include_router(UploadRouter, tags=["Uploader"], prefix="/api/uploader")
app.include_router(ResultsRouter, tags=["Results"], prefix="/api/results")
app.include_router(ValidationRouter, tags=["Validation"], prefix="/api/validation")
app.include_router(CueRouter, tags=["Cue"], prefix='/api/cue')
app.include_router(ExportsRouter, tags=["Exports"], prefix='/api/exports')


@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to the Camai COVID Patient Data OCR System."}


if __name__ == '__main__':
    dotenv.load_dotenv('../.env.backend')
    uvicorn.run('app.main:app', host="0.0.0.0", port=8000, reload=True)
