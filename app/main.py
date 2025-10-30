import datetime

from typing import Any

from fastapi import FastAPI, status
from pydantic import BaseModel

from app.custom_types import (
    ParserSubgraph,
    SupportedProfilerFunction,
    SupportedTaxonomiesFunction,
)
from app.profiling_functions._factory import get_profiler

app = FastAPI()

APP_VERSION = "0.3.0-MLProfile"


class MLProfileMetadata(BaseModel):
    version: str
    generation_date: datetime.datetime
    taxonomy: SupportedTaxonomiesFunction
    profiler: SupportedProfilerFunction


class MLProfileResult(BaseModel):
    name: str
    metadata: MLProfileMetadata
    source: list[Any]  # TODO: fix any
    outputs: dict[str, Any]


class ProfileNotebookParams(BaseModel):
    notebook_file_stem: str
    python_content: str
    parser_elements: list[ParserSubgraph]
    taxonomy_name: SupportedTaxonomiesFunction
    profiler_name: SupportedProfilerFunction


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
    profile_json = MLProfileResult(
        name=params.notebook_file_stem,
        metadata=MLProfileMetadata(
            version=APP_VERSION,
            generation_date=datetime.datetime.now(),
            taxonomy=params.taxonomy_name,
            profiler=params.profiler_name,
        ),
        source=[],
        outputs={},
    )
    prev_step = None

    profiler = get_profiler(
        profile_json.metadata.profiler,
        params.python_content,
        profile_json.metadata.taxonomy,
    )

    for subgraph in params.parser_elements:
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
            "metadata": {}
        }

        if subgraph.step_name == "Library Loading":
            current_step = "Library Loading"
            perplexity = 1
            logprobs = 100
        else:
            current_step, perplexity, logprobs = profiler.profile_subgraph(subgraph, "Others")
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


@app.get(
    "/health",
    tags=["healthcheck"],
    summary="Perform a Health Check",
    response_description="Return HTTP Status Code 200 (OK)",
    status_code=status.HTTP_200_OK,
)
def get_health():
    return "OK"
