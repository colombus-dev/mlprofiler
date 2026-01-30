from abc import ABC, abstractmethod

from app.custom_types import ParserSubgraph
from app.profiling_functions._utils import Taxonomy


class BaseMLProfiler(ABC):

    def __init__(
        self, python_content: str, taxonomy: Taxonomy
    ) -> None:
        super().__init__()

        self.python_content: str = python_content
        self.taxonomy: Taxonomy = taxonomy

    @abstractmethod
    def profile_subgraph(
        self, subgraph: ParserSubgraph, default_step: str
    ) -> tuple[str, float | None, list[list[tuple[str, float]]]]:
        """Profile a given subgraph based on the steps taxonomy.

        Args:
            subgraph (ParserSubgraph): the famix subgraph to profile
            default_step (str): the default step to use when the profiling
                                result is out of the taxonomy

        Returns:
            tuple[str, float | None, list[list[tuple[str, float]]]]: a tuple containing the step,
                                overall perplexity and logprobs for each next token.
                                Default values are used when not using a LLM
        """
