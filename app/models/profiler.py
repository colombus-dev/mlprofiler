from enum import Enum
from pydantic import BaseModel


class ProfilerFunction(str, Enum):
    LLM = "llm"
    DSPIPELINES = "dspipelines"
    HEADERGEN = "headergen"
    EMBEDDING = "embedding"


class ProfileResult(BaseModel):
    step: str
    perplexity: float
    logprobs: list[list[tuple[str, float]]]
