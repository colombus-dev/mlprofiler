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
            "http://localhost:8080/core/api/project",
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
            f"http://localhost:8080/core/api/project/{created_project_id}/notebook/upload/multiple",
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
            f"http://localhost:8080/core/api/project/{project_id}/notebook/{notebook_id}/inconsistencies",
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


def main(student_index: int = 0, notebook_path: str = None):
    """
    Run the experiment process on a single file.

    Args:
        student_index: Index of the student file to process (default: 0)
        notebook_path: Custom path to a notebook file (overrides student_index if provided)
    """
    with httpx.Client(auth=ApiTokenHttpxAuth()) as client:
        console = Console()
        # Creating a new project
        created_project_id = post_project(console, client)

        # Determine file path
        if notebook_path is None:
            notebook_path = f"data/corpus_students/student_{student_index}.ipynb"

        # Importing a notebook and generating its profile
        posted_notebook_profile_id = post_notebook(
            console,
            client,
            created_project_id,
            notebook_path,
        )

        # Get cache response
        cache_response = client.get(
            f"http://localhost:8080/core/api/moose/cache/{posted_notebook_profile_id['notebook_id']}",
        )
        cache_response.raise_for_status()

        # Save cache response
        output_filename = notebook_path.split("/")[-1].replace(".ipynb", "_subgraph.json")
        with open(f"./data/corpus_students/{output_filename}", "w") as f:
            json.dump(cache_response.json(), f)

        # Import LLM profile
        with Progress() as progress:
            progress_task = progress.add_task(
                f"[bold]Importing the llm profile...",
                total=100,
            )

            try:
                # Determine which remap to use
                if notebook_path is None:
                    remapped_result = remap(student_index)
                else:
                    # Extract student index from filename or use 0 as default
                    try:
                        filename = notebook_path.split("/")[-1]
                        if "student_" in filename and ".ipynb" in filename:
                            idx = int(filename.replace("student_", "").replace(".ipynb", ""))
                        else:
                            idx = 0
                        remapped_result = remap(idx)
                    except Exception as e:
                        console.print(f"[bold red]Could not determine student index: {str(e)}, using 0")
                        remapped_result = remap(0)

                # Debug: Print structure of remapped_result
                console.print(f"[bold blue]Remapped result structure: {type(remapped_result)}")
                if isinstance(remapped_result, dict) and "profile" in remapped_result:
                    console.print(f"[bold blue]Profile count: {len(remapped_result['profile'])}")
                    if len(remapped_result['profile']) > 0:
                        sample = remapped_result['profile'][0]
                        console.print(f"[bold blue]First profile item keys: {list(sample.keys())}")
                else:
                    console.print("[bold red]Warning: Unexpected remapped_result structure")

                # Post LLM profile
                profile_url = f"http://localhost:8080/core/api/profiles/{posted_notebook_profile_id['profile_id']}/llm"
                console.print(f"[bold blue]Posting to URL: {profile_url}")

                posted_llm_profile_response = client.post(
                    profile_url,
                    json=remapped_result,
                )

                # Handle response
                if posted_llm_profile_response.status_code != 200:
                    console.print(f"[bold red]HTTP Error: {posted_llm_profile_response.status_code}")
                    console.print(f"[bold red]Response: {posted_llm_profile_response.text}")

                posted_llm_profile_response.raise_for_status()
                console.print("[bold green]Successfully posted LLM profile")
            except FileNotFoundError as e:
                console.print(f"[bold red]File not found error: {str(e)}")
                console.print("[bold yellow]This might be because the subgraph.json file was not created correctly.")
                console.print("[bold yellow]Check that the path in remap_profiles.py matches where the file is saved.")
            except Exception as e:
                console.print(f"[bold red]Error posting LLM profile: {str(e)}")
                console.print("[bold yellow]The process will continue, but inconsistencies might not be available.")
            finally:
                progress.update(progress_task, advance=100)

        # Retrieving generated inconsistencies
        get_inconsistencies(
            console,
            client,
            created_project_id,
            posted_notebook_profile_id["notebook_id"],
        )


if __name__ == "__main__":
    typer.run(main)
