import datetime
from typing import Any
from enum import Enum

from fastapi import APIRouter, FastAPI, File, UploadFile
from pydantic import BaseModel

from app.constants import APP_VERSION, PARSER_API_URL_PREFIX, INFERENCE_API_URL_PREFIX

router = APIRouter()


class TaxonomyFunction(str, Enum):
    DSPIPELINES = "dspipelines"
    DASWOW = "daswow"
    HEADERGEN = "headergen"


class ProfilerFunction(str, Enum):
    LLM = "llm"
    DSPIPELINES = "dspipelines"
    HEADERGEN = "headergen"


@router.post("")
def profile(
        notebook_files: list[UploadFile],
        taxonomy: TaxonomyFunction,
        profiler: ProfilerFunction
    ):
    return []
