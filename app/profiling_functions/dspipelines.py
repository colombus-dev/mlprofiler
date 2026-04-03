import json

from pathlib import Path

from app.custom_types import ParserSubgraph
from app.profiling_functions._base import BaseMLProfiler, Taxonomy

steps_functions_mapping_path = Path(
    "./resources/taxonomies/extra/dspipelines_steps_functions_mapping.json"
)
steps_functions_mapping: dict[str, str] = json.loads(
    steps_functions_mapping_path.read_text()
)


class DSPipelinesProfiler(BaseMLProfiler):
    def __init__(self, python_content: str, taxonomy: Taxonomy):
        super().__init__(python_content, taxonomy)

    async def profile_subgraph(
        self, subgraph: ParserSubgraph, default_step: str, expected: str | list[str] | None = None
    ) -> tuple[str, float | None, list[list[tuple[str, float]]]]:
        retrieved_step = steps_functions_mapping.get(subgraph.function, default_step)
        return (retrieved_step, 1, [[(retrieved_step, 1.0)]])
