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
            f"http://erebe-vm9.i3s.unice.fr:8000/core/api/project/{project_id}/notebook/{notebook_id}/inconsistencies",
            timeout=100,
        )
        progress.update(progress_task, advance=100)

    inconsistencies = get_inconsistencies_response.json()
    if not inconsistencies:
        console.print("[yellow]No inconsistencies found for this notebook.")
        return

    table = Table(title="Inconsistencies")
    table.add_column("ID", style="cyan")
    table.add_column("Detection Date", style="magenta")
    table.add_column("Description", style="green")
    table.add_column("Resolved", style="blue")
    table.add_column("Elements Count", style="yellow")

    for inconsistency in inconsistencies:
        table.add_row(
            inconsistency["inconsistency_id"],
            inconsistency["detection_date"],
            inconsistency["description"],
            str(inconsistency["is_resolved"]),
            str(len(inconsistency["elements"]))
        )

    console.print(table)
    
    # Pour chaque inconsistance, afficher le détail des éléments
    for inconsistency in inconsistencies:
        console.print(f"\n[bold]Details for inconsistency {inconsistency['inconsistency_id']}[/bold]")
        
        elements_table = Table(title="Elements")
        elements_table.add_column("Element ID", style="cyan")
        elements_table.add_column("Library", style="magenta")
        elements_table.add_column("Function", style="green")
        elements_table.add_column("MetaStep", style="blue")
        
        for element in inconsistency["elements"]:
            elements_table.add_row(
                element["notebook_element_id"],
                element["library"] or "-",
                element["function"] or "-",
                element["metastep_name"] or "Unknown"
            )
        
        console.print(elements_table)
        
        # Afficher les décisions s'il y en a
        if inconsistency["decisions"]:
            decisions_table = Table(title="Decisions")
            decisions_table.add_column("Decision ID", style="cyan")
            decisions_table.add_column("Date", style="magenta")
            decisions_table.add_column("Resolution Type", style="green")
            decisions_table.add_column("User", style="blue")
            
            for decision in inconsistency["decisions"]:
                decisions_table.add_row(
                    decision["decision_id"],
                    decision["decision_date"],
                    decision["resolution_type"] or "-",
                    decision["user_name"] or "Anonymous"
                )
            
            console.print(decisions_table)



def get_metrics(console: Console, client: httpx.Client, project_id: str):
    with Progress() as progress:
        progress_task = progress.add_task(
            "[bold]Retrieving some metrics...",
            total=100,
        )
        get_unknown_metrics_response = client.get(
            f"http://erebe-vm9.i3s.unice.fr:8000/core/api/project/{project_id}/metrics/unknown/count",
            timeout=100,
        )
        get_reused_metrics_response = client.get(
            f"http://erebe-vm9.i3s.unice.fr:8000/core/api/project/{project_id}/metrics/reused/count",
            timeout=100,
        )
        get_inconsistencies_metrics_response = client.get(
            f"http://erebe-vm9.i3s.unice.fr:8000/core/api/project/{project_id}/metrics/inconsistencies/count",
            timeout=100,
        )
        progress.update(progress_task, advance=100)

    table = Table(title="Metrics")
    table.add_column("Unknown (count)", style="cyan")
    table.add_column("Reuse (count)", style="magenta")
    table.add_column("Inconsistencies (count)", style="green")

    table.add_row(
        str(get_unknown_metrics_response.json()),
        str(get_reused_metrics_response.json()),
        str(get_inconsistencies_metrics_response.json()),
    )

    console.print(table)


with httpx.Client(auth=ApiTokenHttpxAuth()) as client:
    console = Console()
    # Creating a new project
    created_project_id = post_project(console, client)

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

        # Retrieving metrics
        get_metrics(console, client, created_project_id)

        # Retrieving generated inconsistencies
        get_inconsistencies(
            console,
            client,
            created_project_id,
            posted_notebook_profile_id["notebook_id"],
        )
