import asyncio
import datetime
from typing import Any, Generator

import ujson
from fastapi import APIRouter, UploadFile

from app.constants import APP_VERSION
from app.models.parser import ParserFunction
from app.models.profiler import ProfilerFunction
from app.models.taxonomy import TAXONOMY_BY_NAME, TaxonomyFunction
from app.parsers.factory import get_parser
from app.profiling_functions.factory import get_profiler

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


async def _profile_notebook(
        notebook_file: UploadFile,
        taxonomy_name: TaxonomyFunction,
        profiler_name: ProfilerFunction,
        parser_name: ParserFunction = ParserFunction.VESPUCCI,
):
    file_content = await notebook_file.read()
    source_code = "\n".join(
        c["source"] for c in NotebookCellIterator(file_content.decode("utf8"))
    )

    subgraphs = get_parser(parser_name).parse_code(source_code)

    taxonomy = TAXONOMY_BY_NAME[taxonomy_name]
    profiler = get_profiler(
        profiler_name=profiler_name,
        python_content='',
        taxonomy=taxonomy,
    )
    results = await profiler.profile_multiple_subgraphs(
        subgraphs=subgraphs, default_step=taxonomy.default_step, expected=None
    )

    source: list[dict] = []
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
            "parser": parser_name.value,
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
    profiles = await asyncio.gather(
        *[_profile_notebook(notebook_file, taxonomy, profiler) for notebook_file in notebook_files]
    )
    return profiles
