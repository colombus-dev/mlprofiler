import json

from pathlib import Path

from app.custom_types import ParserSubgraph, SupportedTaxonomiesFunction
from app.profiling_functions._base import BaseMLProfiler

steps_functions_mapping_path = Path(
    "./resources/taxonomies/extra/dspipelines_steps_functions_mapping.json"
)
steps_functions_mapping: dict[str, str] = json.loads(
    steps_functions_mapping_path.read_text()
)


class DSPipelinesProfiler(BaseMLProfiler):

    def __init__(self, python_content: str, taxonomy_name: SupportedTaxonomiesFunction):
        super().__init__(python_content, taxonomy_name)

    def profile_subgraph(
        self, subgraph: ParserSubgraph, default_step: str
    ) -> tuple[str, float | None, list[list[tuple[str, float]]]]:
        retrieved_step = steps_functions_mapping.get(subgraph.function, default_step)
        verified_retrieved_step = (
            retrieved_step
            if retrieved_step in self.taxonomy.get_original_steps_names()
            else default_step
        )
        return (verified_retrieved_step, 1, [[(verified_retrieved_step, 1.0)]])
