from fastapi import FastAPI

from app.constants import APP_VERSION
from app.routers import profile_router

app = FastAPI(version=APP_VERSION)
app.include_router(profile_router.router, prefix="/v2/profile")
