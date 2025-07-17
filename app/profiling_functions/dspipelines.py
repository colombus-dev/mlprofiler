import json

from pathlib import Path

from app.custom_types import ParserSubgraph
from app.profiling_functions._base import BaseMLProfiler

steps_functions_mapping_path = Path(
    "./resources/dspipelines_steps_functions_mapping.json"
)
steps_functions_mapping: dict[str, str] = json.loads(
    steps_functions_mapping_path.read_text()
)


class DSPipelinesProfiler(BaseMLProfiler):

    def __init__(self, python_content: str, taxonomy_name: str):
        super().__init__(python_content, taxonomy_name)

    def profile_subgraph(self, subgraph: ParserSubgraph, default_step: str) -> str:
        retrieved_step = steps_functions_mapping.get(subgraph.function, default_step)
        return retrieved_step if retrieved_step in self.steps_taxonomy else default_step
