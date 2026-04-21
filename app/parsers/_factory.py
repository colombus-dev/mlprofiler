from app.models.parser import ParserFunction
from app.parsers._base import BaseMLParser
from app.parsers.dspipelines import DSPipelinesParser


def get_parser(parser_name: ParserFunction) -> BaseMLParser:
    match parser_name:
        case ParserFunction.DSPIPELINES.value:
            return DSPipelinesParser()
        case _:
            raise ValueError(f"Invalid parser name [{parser_name}].")
