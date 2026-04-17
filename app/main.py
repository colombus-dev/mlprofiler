import datetime

from typing import Any, Annotated

from fastapi import FastAPI, Depends
from pydantic import BaseModel

from app.constants import APP_VERSION
from app.custom_types import (
    ParserSubgraph,
    SupportedParserFunction,
    SupportedProfilerFunction,
)
from app.parsers import get_parser, BaseMLParser
from app.profiling_functions import get_profiler, BaseMLProfiler
from app.profiling_functions._utils import Taxonomy
from app.routers import profile_router

app = FastAPI(version=APP_VERSION)
app.include_router(profile_router.router, prefix="/v2/profile")


# TODO: adapt core_api to /profile API changes


class ParsePythonParams(BaseModel):
    python_content: str
    parser_name: SupportedParserFunction
    parse_subscript: bool


@app.post("/parse")
def parse_python(params: ParsePythonParams) -> list[ParserSubgraph]:
    """Parse the given python code and returns the retrieved subgraphes.

    Parameters
    ----------
    params : ParsePythonParams
        the the python content, parser name and wether to parse subscript
        instructions or not

    Returns
    -------
    list[ParserSubgraph]
        the retrieved subgraphes
    """
    return get_parser(params.parser_name).parse_code(
        params.python_content, params.parse_subscript
    )


class MLProfileMetadata(BaseModel):
    version: str
    generation_date: datetime.datetime
    session_id: str
    taxonomy: str
    profiler: SupportedProfilerFunction
    parser: SupportedParserFunction


class MLProfileResult(BaseModel):
    name: str
    metadata: MLProfileMetadata
    source: list[Any]  # TODO: fix any
    outputs: dict[str, Any]


class ProfileNotebookParams(BaseModel):
    notebook_file_stem: str
    context: str | None = (
        None  # enables profiling subset of python_content (e.g., notebook cell) while keeping the whole context (default: python_content)
    )
    context_truncation_offset: int | None = (
        None  # enables truncating context to avoid context overflow
    )
    instructions_index: list[int] | None = (
        None  # enables profiling subset of ast instructions (e.g., avoid instructions classified as Others by the baseline)
    )
    expected_results: list[str] | list[list[str]] | None = (
        None  # enables giving the baseline result for In-Context Learning (ICL)
    )
    session_id: str | None = None  # enables reusing existing session
    python_content: str
    taxonomy: Taxonomy
    parser_name: SupportedParserFunction
    profiler_name: SupportedProfilerFunction
    parse_subscript: bool


def inject_parser(params: ProfileNotebookParams):
    return get_parser(params.parser_name)


def inject_profiler(params: ProfileNotebookParams):
    return get_profiler(
        params.profiler_name,
        params.context or params.python_content,
        params.taxonomy,
    )


ParserDep = Annotated[BaseMLParser, Depends(inject_parser)]
ProfilerDep = Annotated[BaseMLProfiler, Depends(inject_profiler)]


@app.post("/profile")
async def profile_notebook(
    params: ProfileNotebookParams, parser: ParserDep, profiler: ProfilerDep
) -> MLProfileResult:
    """Compute the ML profile for the given notebook.

    Parameters
    ----------
    params : ProfileNotebookParams
        the notebook file step (e.g. abc/myfile.ipynb -> myfile),
        corresponding python code content and Moose parsing result

    Returns
    -------
    list[Any]
        the LLM profiling result
    """
    context = params.context or params.python_content

    if params.session_id:
        # reusing existing session
        profiler.session_id = params.session_id

    profile_json = MLProfileResult(
        name=params.notebook_file_stem,
        metadata=MLProfileMetadata(
            version=APP_VERSION,
            generation_date=datetime.datetime.now(),
            session_id=profiler.session_id,
            taxonomy=params.taxonomy.name,
            profiler=params.profiler_name,
            parser=params.parser_name,
        ),
        source=[],
        outputs={},
    )
    prev_step = None

    filtered_subgraphes = [
        (i, subgraph)
        for i, subgraph in enumerate(
            parser.parse_code(params.python_content, params.parse_subscript)
        )
        if (params.instructions_index is None) or (i in params.instructions_index)
    ]

    # TODO: improve this part
    expected_results = (
        params.expected_results
        if params.expected_results
        else [None for _ in range(len(filtered_subgraphes))]
    )
    if len(expected_results) != len(filtered_subgraphes):
        expected_results = [expected_results for _ in range(len(filtered_subgraphes))]

    results = (
        await profiler.profile_multiple_subgraphes(
            [fsg for _, fsg in filtered_subgraphes], "Others", expected_results
        )
        if filtered_subgraphes
        else []
    )

    for (i, subgraph), (current_step, perplexity, logprobs) in zip(
        filtered_subgraphes, results
    ):
        # if params.instructions_index and i not in params.instructions_index:
        #     continue

        line = subgraph.source

        res = {
            "id": subgraph.id,
            "algoFamily": None,
            # "algoFamily": algorithms_classified_line["algorithm_family"],
            "algoName": None,
            # "algoName": algorithms_classified_line["algorithm_name"],
            "library": subgraph.library,
            "function": subgraph.function,
            "tasks": [{"name": line, "tasks": []}],
            "metadata": {},
        }

        if params.context_truncation_offset is not None:
            profiler.python_content = "\n".join(
                context.split("\n")[
                    subgraph.start_lineno
                    - 1
                    - params.context_truncation_offset : subgraph.end_lineno
                    + params.context_truncation_offset
                ]
            )

        # if subgraph.step_name == "Library Loading":
        #     current_step = "Library Loading"
        #     perplexity = 1
        #     logprobs = 100
        # else:
        #     if (
        #         current_step == "Library Loading"
        #         and subgraph.step_name != "Library Loading"
        #     ):
        #         current_step = "Others"

        res["metadata"]["perplexity"] = perplexity
        res["metadata"]["logprobs"] = logprobs

        if prev_step == current_step:
            profile_json.source[-1]["tasks"].append(res)
        else:
            profile_json.source.append(
                {
                    "name": current_step,
                    "tasks": [res],
                    "outputs_ids": [],
                }
            )
        prev_step = current_step

    return profile_json
