import asyncio
import datetime

from fastapi import APIRouter

from app.constants import APP_VERSION
from app.models.notebooks import NotebookInformation, NotebookList
from app.models.profiler import ProfilerFunction
from app.models.taxonomy import TAXONOMY_BY_NAME, TaxonomyFunction
from app.profiling_functions.factory import get_profiler

router = APIRouter()

async def _profile_notebook(
        notebook_info: NotebookInformation,
        taxonomy_name: TaxonomyFunction,
        profiler_name: ProfilerFunction,
):
    """
        Return the profile of a notebook file (represented by the object containing all needed information) given a profiling function and a taxonomy
    """

    parser_model = notebook_info.parser_model
    taxonomy = TAXONOMY_BY_NAME[taxonomy_name]
    profiler = get_profiler(notebook_info.source_code, taxonomy, profiler_name)
    results = await profiler.profile_multiple_subgraphs(parser_model)

    source: list[dict] = []
    for subgraph, profiler_result in zip(parser_model, results):
        element = {
            "id": subgraph.id,
            "algoFamily": None,
            "algoName": None,
            "library": subgraph.library,
            "function": subgraph.function,
            "tasks": [{"name": subgraph.source, "tasks": []}],
            "metadata": {"perplexity": profiler_result.perplexity},
        }
        if source and source[-1]["name"] == profiler_result.step:
            source[-1]["tasks"].append(element)
        else:
            step = {"name": profiler_result.step, "tasks": [element], "outputs_ids": []}
            source.append(step)
    return {
        "name": notebook_info.name,
        "metadata": {
            "version": APP_VERSION,
            "generation_date": datetime.datetime.now().isoformat(),
            "session_id": profiler.session_id,
            "taxonomy": taxonomy_name,
            "profiler": profiler_name,
            "parser": notebook_info.parser_function,
        },
        "source": source,
        "outputs": {},
    }


@router.post("")
async def profile(
        list_of_notebooks: NotebookList,
        taxonomy: TaxonomyFunction,
        profiler: ProfilerFunction,
):
    """
    Endpoint to get files' profiles according to their FAST model representation and given a profiler and a taxonomy
    """
    profiles = await asyncio.gather(
        *[_profile_notebook(notebook, taxonomy, profiler) for notebook in list_of_notebooks.data]
    )
    return profiles
