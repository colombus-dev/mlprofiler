from collections import Counter

import httpx

from app.models.parser import ParserSubgraph
from app.models.profiler import ProfileResult
from app.profiling_functions.base import BaseMLProfiler, Taxonomy


class HeaderGenProfiler(BaseMLProfiler):
    def __init__(self, source_code: str, taxonomy: Taxonomy):
        super().__init__(source_code, taxonomy)

    async def profile_subgraph(self, subgraph: ParserSubgraph) -> ProfileResult:
        # TODO: add docstring to payload for fair comparison
        ml_label_response = httpx.post(
            "http://headergen:54068/get_ml_labels",
            json={f"{subgraph.library}.{subgraph.function}": {"docstring": ""}},
        )
        if ml_label_response.is_error:
            return ProfileResult(
                step=self.taxonomy.default_step,
                perplexity=1
            )
        retrieved_steps: list[str] = ml_label_response.json()
        if not retrieved_steps:
            return ProfileResult(
                step=self.taxonomy.default_step,
                perplexity=1
            )
        retrieved_steps_counter = Counter(retrieved_steps)
        # TODO: currently only supporting the first step
        retrieved_step = retrieved_steps_counter.most_common(1)[0][0]
        return ProfileResult(
            step=retrieved_step,
            perplexity=1
        )
