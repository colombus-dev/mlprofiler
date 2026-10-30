from pydantic import BaseModel

from app.models.parser import ParserSubgraph


class NotebookInformation(BaseModel):
    "Groups all information about a notebook in one object"

    name: str
    parser_model: list[ParserSubgraph]
    source_code: str
    parser_function: str

class NotebookList(BaseModel):
    data: list[NotebookInformation]
