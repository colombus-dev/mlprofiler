import httpx

from app.custom_types import ParserSubgraph
from app.profiling_functions._base import BaseMLProfiler


class HeaderGenProfiler(BaseMLProfiler):

    def __init__(self, python_content: str, taxonomy_name: str):
        super().__init__(python_content, taxonomy_name)

    def profile_subgraph(self, subgraph: ParserSubgraph, default_step: str) -> str:
        # TODO: add docstring to payload for fair comparison
        ml_label_response = httpx.post(
            "http://headergen:54068/get_ml_labels",
            json={f"{subgraph.library}.{subgraph.function}": {"docstring": ""}},
        )
        if ml_label_response.is_error:
            return default_step
        retrieved_step = ml_label_response.json()
        return retrieved_step if retrieved_step in self.steps_taxonomy else default_step
