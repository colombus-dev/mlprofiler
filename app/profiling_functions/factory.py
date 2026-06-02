from app.models.profiler import ProfilerFunction
from app.profiling_functions.base import BaseMLProfiler, Taxonomy
from app.profiling_functions.dspipelines import DSPipelinesProfiler
from app.profiling_functions.embedding import EmbeddingProfiler
from app.profiling_functions.headergen import HeaderGenProfiler
from app.profiling_functions.llm import LLMProfiler


def get_profiler(source_code: str, taxonomy: Taxonomy, profiler_name: ProfilerFunction) -> BaseMLProfiler:
    match profiler_name:
        case "embedding":
            return EmbeddingProfiler(source_code=source_code, taxonomy=taxonomy)
        case "llm":
            return LLMProfiler(source_code=source_code, taxonomy=taxonomy)
        case "dspipelines":
            return DSPipelinesProfiler(source_code=source_code, taxonomy=taxonomy)
        case "headergen":
            return HeaderGenProfiler(source_code=source_code, taxonomy=taxonomy)
        case _:
            raise ValueError(f"Invalid profiler name [{profiler_name}].")
