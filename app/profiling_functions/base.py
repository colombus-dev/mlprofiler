import asyncio
import uuid
from abc import ABC, abstractmethod

from app.models.parser import ParserSubgraph
from app.models.profiler import ProfileResult
from app.models.taxonomy import Taxonomy

MAXIMUM_LINE_SIZE = 10
MAXIMUM_LINE_LENGTH = 79  # Use PEP standard to trim long lines https://peps.python.org/pep-0008/#maximum-line-length



class BaseMLProfiler(ABC):
    def __init__(self, source_code: str, taxonomy: Taxonomy):
        super().__init__()
        self._taxonomy: Taxonomy = taxonomy
        self._source_code = source_code
        self._source_code_split = self._source_code.split('\n')
        self._session_id = f"session-{uuid.uuid4().__str__()}"

    @property
    def taxonomy(self):
        return self._taxonomy

    @property
    def source_code(self):
        return self._source_code

    @property
    def session_id(self):
        return self._session_id

    def compute_source_code_context(self, target_line: int, size: int = MAXIMUM_LINE_SIZE):
        from_line = max(0, target_line - size)
        to_line = min(len(self._source_code_split), target_line + size)

        context = self._source_code_split[from_line:to_line]
        context = [c[:MAXIMUM_LINE_LENGTH] for c in context]

        return '\n'.join(context)

    @abstractmethod
    async def profile_subgraph(self, subgraph: ParserSubgraph) -> ProfileResult:
        ...

    async def profile_multiple_subgraphs(self, subgraphs: list[ParserSubgraph]) -> list[ProfileResult]:
        return await asyncio.gather(*(self.profile_subgraph(subgraph) for subgraph in subgraphs))
