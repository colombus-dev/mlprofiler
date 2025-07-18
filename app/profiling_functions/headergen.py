import httpx

from collections import Counter

from app.custom_types import ParserSubgraph, SupportedTaxonomiesFunction
from app.profiling_functions._base import BaseMLProfiler


class HeaderGenProfiler(BaseMLProfiler):

    def __init__(self, python_content: str, taxonomy_name: SupportedTaxonomiesFunction):
        super().__init__(python_content, taxonomy_name)

    def profile_subgraph(self, subgraph: ParserSubgraph, default_step: str) -> str:
        # TODO: add docstring to payload for fair comparison
        ml_label_response = httpx.post(
            "http://headergen:54068/get_ml_labels",
            json={f"{subgraph.library}.{subgraph.function}": {"docstring": ""}},
        )
        if ml_label_response.is_error:
            return default_step
        retrieved_steps = ml_label_response.json()
        compatible_steps = [
            step for step in retrieved_steps if step in self.steps_taxonomy
        ]
        if not compatible_steps:
            return default_step
        compatible_steps_counter = Counter(compatible_steps)
        # TODO: currently only supporting the first step
        return compatible_steps_counter.most_common(1)[0][0]
