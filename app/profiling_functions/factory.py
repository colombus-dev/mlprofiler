from app.models.profiler import ProfilerFunction
from app.profiling_functions.base import BaseMLProfiler, Taxonomy
from app.profiling_functions.dspipelines import DSPipelinesProfiler
from app.profiling_functions.embedding import EmbeddingProfiler
from app.profiling_functions.headergen import HeaderGenProfiler
from app.profiling_functions.llm import LLMProfiler


def get_profiler(
        profiler_name: ProfilerFunction,
        taxonomy: Taxonomy,
        source_code: str
) -> BaseMLProfiler:
    match profiler_name:
        case "embedding":
            return EmbeddingProfiler(taxonomy=taxonomy, source_code=source_code)
        case "llm":
            return LLMProfiler(taxonomy=taxonomy, source_code=source_code)
        case "dspipelines":
            return DSPipelinesProfiler(taxonomy=taxonomy, source_code=source_code)
        case "headergen":
            return HeaderGenProfiler(taxonomy=taxonomy, source_code=source_code)
        case _:
            raise ValueError(f"Invalid profiler name [{profiler_name}].")
