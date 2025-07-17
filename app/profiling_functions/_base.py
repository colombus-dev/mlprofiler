from abc import ABC, abstractmethod

from app.custom_types import ParserSubgraph
from app.profiling_functions._utils import load_taxonomy


class BaseMLProfiler(ABC):

    def __init__(self, python_content: str, taxonomy_name: str) -> None:
        super().__init__()

        self.python_content = python_content
        self.steps_taxonomy = load_taxonomy(taxonomy_name)

    @abstractmethod
    def profile_subgraph(self, subgraph: ParserSubgraph, default_step: str) -> str: ...
