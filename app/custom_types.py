from typing import Any, Literal

from pydantic import BaseModel, TypeAdapter


class ParserSubgraph(BaseModel):
    id: str
    library: str
    function: str
    value: dict[str, Any]
    source: str
    start_lineno: int
    end_lineno: int
    step_name: str


ParserSubgraphListAdapter = TypeAdapter(list[ParserSubgraph])


SupportedTaxonomiesFunction = Literal["headergen", "dspipelines", "daswow"]
SupportedParserFunction = Literal["dspipelines"]
SupportedProfilerFunction = Literal["embedding", "llm", "dspipelines", "headergen"]
