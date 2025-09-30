import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import models
from .database import engine
from .api.v1.api import api_router as api_router_v1
from .api.setup_router import setup_router

# models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="ISP Framework API",
    description="Comprehensive API for ISP operations.",
    version="1.0.0"
)

origins = os.getenv("CORS_ORIGINS", "http://localhost:5174,http://10.120.120.29:5174,http://160.119.127.237:5174").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the setup router (unversioned)
app.include_router(setup_router, prefix="/api/setup", tags=["setup"])

# Include the version 1 of the API
app.include_router(api_router_v1, prefix="/api/v1")

@app.get("/")
def read_root():
    return {"message": "Welcome to the ISP Framework API"}