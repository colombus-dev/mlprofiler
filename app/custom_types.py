from typing import Any, Literal

from pydantic import BaseModel, TypeAdapter


class ParserSubgraph(BaseModel):
    # TODO: move this to common and use it in mock and core
    id: str
    library: str
    function: str
    value: dict[str, Any]
    source: str
    step_name: str


ParserSubgraphListAdapter = TypeAdapter(list[ParserSubgraph])


SupportedTaxonomiesFunction = Literal["headergen", "dspipelines"]
SupportedProfilerFunction = Literal["llm", "dspipelines"]
