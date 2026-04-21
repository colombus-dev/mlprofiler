import datetime
from typing import Any, Generator, List

import httpx
import ujson
from fastapi import APIRouter, UploadFile

from app.constants import APP_VERSION, PARSER_API_TIMEOUT, PARSER_API_URL_PREFIX
from app.models.parser import ParserFunction, ParserSubgraph
from app.models.profiler import ProfilerFunction
from app.models.taxonomy import TAXONOMY_BY_NAME, TaxonomyFunction
from app.profiling_functions import get_profiler

router = APIRouter()


class NotebookCellIterator:
    def __init__(self, content_raw: str):
        self._content_parsed = ujson.loads(content_raw)
        self._generator = self._iterate_cells()

    def __iter__(self):
        self._generator = self._iterate_cells()
        return self

    def __next__(self) -> dict:
        return next(self._generator)

    def _iterate_cells(self) -> Generator[dict, Any, None]:
        # yield only cells with source code, also transform source code to str
        for cell in self._content_parsed["cells"]:
            if cell["cell_type"] == "code":
                if isinstance(cell["source"], list):
                    cell["source"] = "".join(cell["source"])
                if cell["source"]:
                    yield cell


def _parse_source_code(source_code: str) -> List[ParserSubgraph]:
    parser_response = httpx.post(
        f"{PARSER_API_URL_PREFIX}/parse",
        json={
            "source": source_code,
        },
        timeout=PARSER_API_TIMEOUT,
    )
    parser_response.raise_for_status()
    parser_response = parser_response.json()
    return [ParserSubgraph.model_validate(pr) for pr in parser_response]


async def _profile_notebook(
    notebook_file: UploadFile,
    taxonomy_name: TaxonomyFunction,
    profiler_name: ProfilerFunction,
):
    file_content = await notebook_file.read()
    source_code = "\n".join(
        c["source"] for c in NotebookCellIterator(file_content.decode("utf8"))
    )

    subgraphs = _parse_source_code(source_code)

    taxonomy = TAXONOMY_BY_NAME[taxonomy_name]
    profiler = get_profiler(
        profiler_name=profiler_name,
        python_content=source_code,
        taxonomy=taxonomy,
    )
    results = await profiler.profile_multiple_subgraphes(
        subgraphes=subgraphs, default_step=taxonomy.default_step, expected=None
    )

    source = []
    for subgraph, (current_step, perplexity, logprobs) in zip(subgraphs, results):
        element = {
            "id": subgraph.id,
            "algoFamily": None,
            "algoName": None,
            "library": subgraph.library,
            "function": subgraph.function,
            "tasks": [{"name": subgraph.source, "tasks": []}],
            "metadata": {"perplexity": perplexity, "logprobs": logprobs},
        }
        if source and source[-1]["name"] == current_step:
            source[-1]["tasks"].append(element)
        else:
            step = {"name": current_step, "tasks": [element], "outputs_ids": []}
            source.append(step)
    return {
        "name": notebook_file.filename,
        "metadata": {
            "version": APP_VERSION,
            "generation_date": datetime.datetime.now().isoformat(),
            "session_id": profiler.session_id,
            "taxonomy": taxonomy_name,
            "profiler": profiler_name,
            "parser": ParserFunction.VESPUCCI.value,
        },
        "source": source,
        "outputs": {},
    }


@router.post("")
async def profile(
    notebook_files: list[UploadFile],
    taxonomy: TaxonomyFunction,
    profiler: ProfilerFunction,
):
    profiles = []
    for notebook_file in notebook_files:
        profiles.append(await _profile_notebook(notebook_file, taxonomy, profiler))
    return profiles
