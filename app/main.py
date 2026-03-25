import datetime

from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel

from app.custom_types import (
    SupportedParserFunction,
    SupportedProfilerFunction,
)
from app.parsers import get_parser
from app.profiling_functions import get_profiler
from app.profiling_functions._utils import Taxonomy

app = FastAPI()

# TODO: adapt core_api to /profile API changes

APP_VERSION = "0.4.0-MLProfile"


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


@app.post("/profile")
def profile_notebook(params: ProfileNotebookParams) -> MLProfileResult:
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
    parser = get_parser(params.parser_name)

    context = params.context or params.python_content
    profiler = get_profiler(
        params.profiler_name,
        context,
        params.taxonomy,
    )

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
        if (not params.instructions_index) or (i in params.instructions_index)
    ]

    # TODO: improve this part
    expected_results = (
        params.expected_results
        if params.expected_results
        else [None for _ in range(len(filtered_subgraphes))]
    )
    if len(expected_results) != len(filtered_subgraphes):
        expected_results = [expected_results for _ in range(len(filtered_subgraphes))]

    # print(expected_results)

    for (i, subgraph), expected in zip(filtered_subgraphes, expected_results):
        if params.instructions_index and i not in params.instructions_index:
            continue

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

        if subgraph.step_name == "Library Loading":
            current_step = "Library Loading"
            perplexity = 1
            logprobs = 100
        else:
            current_step, perplexity, logprobs = profiler.profile_subgraph(
                subgraph, "Others", expected
            )
            if (
                current_step == "Library Loading"
                and subgraph.step_name != "Library Loading"
            ):
                current_step = "Others"

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
