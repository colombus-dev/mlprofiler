from app.custom_types import SupportedProfilerFunction
from app.profiling_functions._base import BaseMLProfiler
from app.profiling_functions.dspipelines import DSPipelinesProfiler
from app.profiling_functions.llm import LLMProfiler


def get_profiler(
    profiler_name: SupportedProfilerFunction,
    python_content: str,
    taxonomy_name: str,
) -> BaseMLProfiler:
    match (profiler_name):
        case "llm":
            return LLMProfiler(
                python_content=python_content, taxonomy_name=taxonomy_name
            )
        case "dspipelines":
            return DSPipelinesProfiler(
                python_content=python_content, taxonomy_name=taxonomy_name
            )
        case _:
            raise ValueError(f"Invalid profiler name [{profiler_name}].")
