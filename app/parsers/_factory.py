from app.custom_types import SupportedParserFunction
from app.parsers._base import BaseMLParser
from app.parsers.dspipelines import DSPipelinesParser


def get_parser(parser_name: SupportedParserFunction) -> BaseMLParser:
    match parser_name:
        case "dspipelines":
            return DSPipelinesParser()
        case _:
            raise ValueError(f"Invalid parser name [{parser_name}].")
