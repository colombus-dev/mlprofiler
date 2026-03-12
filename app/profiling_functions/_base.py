import uuid

from abc import ABC, abstractmethod

from app.custom_types import ParserSubgraph
from app.profiling_functions._utils import Taxonomy


class BaseMLProfiler(ABC):
    def __init__(self, python_content: str, taxonomy: Taxonomy) -> None:
        super().__init__()

        self._python_content: str = python_content
        self.taxonomy: Taxonomy = taxonomy
        self.session_id = f"session-{uuid.uuid4()}"
    
    @property
    def python_content(self):
        return self._python_content

    @python_content.setter
    def python_content(self, new_content):
        self._python_content = new_content

    @abstractmethod
    def profile_subgraph(
        self, subgraph: ParserSubgraph, default_step: str, expected: str | list[str] | None = None
    ) -> tuple[str, float | None, list[list[tuple[str, float]]]]:
        """Profile a given subgraph based on the steps taxonomy.

        Args:
            subgraph (ParserSubgraph): the famix subgraph to profile
            default_step (str): the default step to use when the profiling
                                result is out of the taxonomy
            expected (str): the expected step (given by the baseline)

        Returns:
            tuple[str, float | None, list[list[tuple[str, float]]]]: a tuple containing the step,
                                overall perplexity and logprobs for each next token.
                                Default values are used when not using a LLM
        """
