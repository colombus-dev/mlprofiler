import json
from pathlib import Path

from app.models.parser import ParserSubgraph
from app.models.profiler import ProfileResult
from app.profiling_functions.base import BaseMLProfiler, Taxonomy

steps_functions_mapping_path = Path(
    "./resources/taxonomies/extra/dspipelines_steps_functions_mapping.json"
)
steps_functions_mapping: dict[str, str] = json.loads(
    steps_functions_mapping_path.read_text()
)


class DSPipelinesProfiler(BaseMLProfiler):
    def __init__(self, taxonomy: Taxonomy, source_code: str):
        super().__init__(taxonomy, source_code)

    async def profile_subgraph(self, subgraph: ParserSubgraph) -> ProfileResult:
        retrieved_step = steps_functions_mapping.get(subgraph.function, self.taxonomy.default_step)
        return ProfileResult(step=retrieved_step, perplexity=1, logprobs=[[(retrieved_step, 1.0)]])
