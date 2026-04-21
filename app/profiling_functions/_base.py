import asyncio
import uuid
from abc import ABC, abstractmethod

from app.models.parser import ParserSubgraph
from app.models.taxonomy import Taxonomy


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
    async def profile_subgraph(
        self,
        subgraph: ParserSubgraph,
        default_step: str,
        expected: str | list[str] | None = None,
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

    async def profile_multiple_subgraphes(
        self,
        subgraphes: list[ParserSubgraph],
        default_step: str,
        expected: list[str | list[str]] | None = None,
    ) -> list[tuple[str, float | None, list[list[tuple[str, float]]]]]:
        """Profile a given list of subgraphes based on the steps taxonomy.

        Args:
            subgraphes (list[ParserSubgraph]): the list of famix subgraphes to profile
            default_step (str): the default step to use when the profiling
                                result is out of the taxonomy
            expected (str): the expected steps (given by the baseline)

        Returns:
            list[tuple[str, float | None, list[list[tuple[str, float]]]]]: the list of tuples containing the step,
                                overall perplexity and logprobs for each next token.
                                Default values are used when not using a LLM
        """
        expected_steps = (
            expected
            if isinstance(expected, list)
            else [None for _ in range(len(subgraphes))]
        )
        return await asyncio.gather(
            *(
                self.profile_subgraph(subgraph, default_step, exp)
                for subgraph, exp in zip(subgraphes, expected_steps)
            )
        )
