from collections import Counter

import httpx

from app.models.parser import ParserSubgraph
from app.profiling_functions.base import BaseMLProfiler, Taxonomy


class HeaderGenProfiler(BaseMLProfiler):
    def __init__(self, python_content: str, taxonomy: Taxonomy):
        super().__init__(python_content, taxonomy)

    async def profile_subgraph(
            self,
            subgraph: ParserSubgraph,
            default_step: str,
            expected: str | list[str] | None = None,
    ) -> tuple[str, float | None, list[list[tuple[str, float]]]]:
        # TODO: add docstring to payload for fair comparison
        ml_label_response = httpx.post(
            "http://headergen:54068/get_ml_labels",
            json={f"{subgraph.library}.{subgraph.function}": {"docstring": ""}},
        )
        if ml_label_response.is_error:
            return (default_step, 1, [[(default_step, 1.0)]])
        retrieved_steps: list[str] = ml_label_response.json()
        if not retrieved_steps:
            return (default_step, 1, [[(default_step, 1.0)]])
        retrieved_steps_counter = Counter(retrieved_steps)
        # TODO: currently only supporting the first step
        retrieved_step = retrieved_steps_counter.most_common(1)[0][0]
        return (retrieved_step, 1, [[(retrieved_step, 1.0)]])
