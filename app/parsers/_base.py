from abc import ABC, abstractmethod

from app.custom_types import ParserSubgraph


class BaseMLParser(ABC):
    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def parse_code(self, python_code: str, parse_subscript: bool = True) -> list[ParserSubgraph]:
        """Parse a given python code to extract the instructions to classify.

        Args:
            python_code (str): the python code to parse
            parse_subscript (bool): whether to parse subscripts instructions or not (e.g., df[...])

        Returns:
            list[ParserSubgraph]: the retrieved subgraphes from the given code
        """
