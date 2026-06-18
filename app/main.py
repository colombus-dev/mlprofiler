import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.profiling_functions.embedding import (
    EmbeddingModelSingleton,
    InferenceSessionSingleton,
)
from app.routers import profile_router
from app.settings import get_settings

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await asyncio.to_thread(EmbeddingModelSingleton.get_instance, "Qwen/Qwen3-Embedding-0.6B")
    await asyncio.to_thread(InferenceSessionSingleton.get_instance, "resources/SVC_mlpipelines_classifier_model.onnx")
    yield


app = FastAPI(version=settings.app_version, lifespan=lifespan)
app.include_router(profile_router.router, prefix="/v2/profile")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
