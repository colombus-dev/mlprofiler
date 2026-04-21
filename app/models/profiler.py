from enum import Enum


class ProfilerFunction(str, Enum):
    LLM = "llm"
    DSPIPELINES = "dspipelines"
    HEADERGEN = "headergen"
