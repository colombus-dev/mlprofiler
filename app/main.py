import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.constants import APP_VERSION
from app.profiling_functions.embedding import (
    EmbeddingModelSingleton,
    InferenceSessionSingleton,
)
from app.routers import profile_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await asyncio.to_thread(EmbeddingModelSingleton.get_instance, "Qwen/Qwen3-Embedding-0.6B")
    InferenceSessionSingleton.get_instance("resources/SVC_mlpipelines_classifier_model.onnx")
    yield


app = FastAPI(version=APP_VERSION, lifespan=lifespan)
app.include_router(profile_router.router, prefix="/v2/profile")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
