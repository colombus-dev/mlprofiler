from fastapi import FastAPI

from app.routers import profile_router
from app.settings import get_settings

settings = get_settings()


app = FastAPI(version=settings.app_version)
app.include_router(profile_router.router, prefix="/v2/profile")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
