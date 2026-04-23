from app.models.profiler import ProfilerFunction
from app.profiling_functions._base import BaseMLProfiler, Taxonomy
from app.profiling_functions.dspipelines import DSPipelinesProfiler
from app.profiling_functions.embedding import EmbeddingProfiler
from app.profiling_functions.headergen import HeaderGenProfiler
from app.profiling_functions.llm import LLMProfiler


def get_profiler(
    profiler_name: ProfilerFunction,
    python_content: str,
    taxonomy: Taxonomy,
) -> BaseMLProfiler:
    match profiler_name:
        case "embedding":
            return EmbeddingProfiler(python_content=python_content, taxonomy=taxonomy)
        case "llm":
            return LLMProfiler(python_content=python_content, taxonomy=taxonomy)
        case "dspipelines":
            return DSPipelinesProfiler(python_content=python_content, taxonomy=taxonomy)
        case "headergen":
            return HeaderGenProfiler(python_content=python_content, taxonomy=taxonomy)
        case _:
            raise ValueError(f"Invalid profiler name [{profiler_name}].")
