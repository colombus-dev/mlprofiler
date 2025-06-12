import json
import subprocess
import sys
import time

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



def post_inconsistencies_curl(
    console: Console, project_id: str, notebook_id: str
):
    import subprocess
    import json
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

    # Prepare curl command parameters
    curl_data = json.dumps({
        "notebookId": notebook_id,
        "projectId": project_id
    })

    # Create a custom progress display
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        TimeElapsedColumn(),
    ) as progress:
        # Add task that will run indefinitely until the curl command completes
        progress_task = progress.add_task(
            "[bold]Retrieving inconsistencies...", total=None
        )

        # Execute curl command with subprocess
        try:
            result = subprocess.run(
                [
                    "curl", "-X", "POST",
                    "-H", "Content-Type: application/json",
                    "-d", curl_data,
                    "http://localhost:1701/inconsistencies"
                ],
                capture_output=True,
                text=True,
                check=True
            )

            # Process completed
            progress.stop_task(progress_task)

            # Try to parse the response
            try:
                response_data = json.loads(result.stdout)
                console.print(f"[bold green]Successfully created inconsistencies")

                # Display the number of inconsistencies inserted
                if isinstance(response_data, dict) and "count" in response_data:
                    console.print(f"[bold green]Number of inconsistencies inserted: {response_data['count']}")
                elif isinstance(response_data, int):
                    console.print(f"[bold green]Number of inconsistencies inserted: {response_data}")
                else:
                    console.print(f"[bold yellow]Response received: {response_data}")
            except json.JSONDecodeError:
                console.print("[bold yellow]Could not parse JSON response. Raw output:")
                console.print(result.stdout)

        except subprocess.CalledProcessError as e:
            console.print(f"[bold red]Error calling curl: {e}")
            console.print(f"[bold red]Command output: {e.stdout}")
            console.print(f"[bold red]Error output: {e.stderr}")


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

        with Progress() as progress:
            delay_seconds = 20
            delay_task = progress.add_task("[bold yellow]Waiting for inconsistencies to be calculated...", total=delay_seconds)
            for _ in range(delay_seconds):
                time.sleep(1)
                progress.update(delay_task, advance=1)
            console.print("[bold green]Delay complete, retrieving inconsistencies...")

        get_inconsistencies(
            console,
            client,
            created_project_id,
            posted_notebook_profile_id["notebook_id"],
        )


if __name__ == "__main__":
    typer.run(main)
