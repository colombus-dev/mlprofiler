import json
import subprocess
import sys

import httpx
import typer

from rich.console import Console
from rich.progress import Progress
from rich.table import Table

from remap_profiles import remap

sys.path.append("..")

from common.auth import ApiTokenHttpxAuth

app = typer.Typer()


def post_project(console: Console, client: httpx.Client):
    with Progress() as progress:
        progress_task = progress.add_task("[bold]Creating a new project...", total=100)
        created_project_response = client.post(
            "http://erebe-vm9.i3s.unice.fr:8000/core/api/project",
            json={"name": "demo-llm-manually"},
        )
        progress.update(progress_task, advance=100)
        created_project_id = created_project_response.json()
    console.print("Created project ID:", created_project_id)
    return created_project_id


def post_notebook(
    console: Console,
    client: httpx.Client,
    created_project_id: str,
    notebook_path: str,
    timeout=360,
):
    with Progress() as progress:
        progress_task = progress.add_task(
            f"[bold]Importing the notebook ({notebook_path})...",
            total=100,
        )
        posted_notebook_response = client.post(
            f"http://erebe-vm9.i3s.unice.fr:8000/core/api/project/{created_project_id}/notebook/upload/multiple",
            files={"notebook_files": open(notebook_path, "rb")},
            timeout=timeout,
        )
        progress.update(progress_task, advance=100)
        if posted_notebook_response.is_error:
            console.print(posted_notebook_response)
            subprocess.run(["docker", "ps"])
            return
        posted_notebook = posted_notebook_response.json()
    console.print("Created notebook:")
    console.print_json(data=posted_notebook)
    return posted_notebook[0]


def get_inconsistencies(
    console: Console, client: httpx.Client, project_id: str, notebook_id: str
):
    with Progress() as progress:
        progress_task = progress.add_task(
            "[bold]Retrieving generated inconsistencies...",
            total=100,
        )
        get_inconsistencies_response = client.get(
            f"http://erebe-vm9.i3s.unice.fr:8080/core/api/project/{project_id}/notebook/{notebook_id}/inconsistencies",
            timeout=100,
        )
        progress.update(progress_task, advance=100)

    table = Table(title="Inconsistencies")
    table.add_column("Position", style="cyan")
    table.add_column("StepImpl IDs", style="magenta")
    table.add_column("MetaStep Names", style="green")

    for inconsistency in get_inconsistencies_response.json():
        table.add_row(*[str(e) for e in inconsistency.values()])

    console.print(table)


with httpx.Client(auth=ApiTokenHttpxAuth()) as client:
    console = Console()
    # Creating a new project
    # created_project_id = "ab95d3bb-5333-4b9b-9fc4-eb60cb91eed3"
    created_project_id = post_project(console, client)
    # Populating db with famix entities
    famix_entity_invoc_response = client.post(
        f"http://erebe-vm9.i3s.unice.fr:8000/vespucci/api/typesgs",
        json={"name": "Invocation", "value": "Famix-Python-Entities.Invocation"},
    )
    famix_entity_invoc_response.raise_for_status()
    famix_entity_import_response = client.post(
        f"http://erebe-vm9.i3s.unice.fr:8000/vespucci/api/typesgs",
        json={"name": "Import", "value": "Famix-Python-Entities.Import"},
    )
    famix_entity_import_response.raise_for_status()

    for i in [0, 1, 3, 4, 5]:
        # Importing a notebook and generating its profile
        posted_notebook_profile_id = post_notebook(
            console,
            client,
            created_project_id,
            f"data/corpus_students/student_{i}.ipynb",
        )
        # TODO: manually import LLM results
        cache_response = client.get(
            f"http://erebe-vm9.i3s.unice.fr:8000/core/api/moose/cache/{posted_notebook_profile_id['notebook_id']}",
        )
        cache_response.raise_for_status()
        with open(f"./data/corpus_students/student_{i}_subgraph.json", "w") as f:
            json.dump(cache_response.json(), f)
        with Progress() as progress:
            progress_task = progress.add_task(
                f"[bold]Importing the llm profile (./out/data/corpus_students/student_{i}_llm_final.json)...",
                total=100,
            )
            remapped_result = remap(i)

            posted_llm_profile_response = client.post(
                f"http://erebe-vm9.i3s.unice.fr:8000/core/api/profiles/{posted_notebook_profile_id['profile_id']}/llm",
                json=remapped_result,
            )
            posted_llm_profile_response.raise_for_status()
            progress.update(progress_task, advance=100)
        # # Retrieving generated inconsistencies
        # get_inconsistencies(
        #     console,
        #     client,
        #     created_project_id,
        #     posted_notebook_profile_id["notebook_id"],
        # )
