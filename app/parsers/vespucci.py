import httpx

from app.constants import PARSER_API_URL_PREFIX
from app.models.parser import ParserSubgraph
from app.parsers.base import BaseMLParser

PARSER_API_TIMEOUT = 2


class VespucciParser(BaseMLParser):
    def __init__(self):
        super().__init__()

    def parse_code(
            self, python_code: str, parse_subscript: bool = True
    ) -> list[ParserSubgraph]:
        parser_response = httpx.post(
            f"{PARSER_API_URL_PREFIX}/parse",
            json={
                "source": python_code,
            },
            timeout=PARSER_API_TIMEOUT,
        )
        parser_response.raise_for_status()
        parser_response = parser_response.json()
        return sorted([ParserSubgraph.model_validate(pr) for pr in parser_response], key=lambda pr: pr.line.start)
