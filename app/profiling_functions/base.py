import asyncio
import uuid
from abc import ABC, abstractmethod

from app.models.parser import ParserSubgraph
from app.models.profiler import ProfileResult
from app.models.taxonomy import Taxonomy


class BaseMLProfiler(ABC):
    def __init__(self, taxonomy: Taxonomy, source_code: str):
        super().__init__()
        self.taxonomy: Taxonomy = taxonomy
        self.source_code = source_code
        self._source_code_split = self.source_code.split('\n')
        self.session_id = f"session-{uuid.uuid4().__str__()}"

    def truncate_source_code(self, target_line: int, size: int = 10):
        from_line = max(0, target_line - size)
        to_line = min(len(self._source_code_split), target_line + size)
        return '\n'.join(self._source_code_split[from_line:to_line])

    @abstractmethod
    async def profile_subgraph(self, subgraph: ParserSubgraph) -> ProfileResult:
        ...

    async def profile_multiple_subgraphs(self, subgraphs: list[ParserSubgraph]) -> list[ProfileResult]:
        return await asyncio.gather(*(self.profile_subgraph(subgraph) for subgraph in subgraphs))
