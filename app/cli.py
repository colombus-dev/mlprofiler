import httpx
import json
import os

import typer

from pathlib import Path
from tqdm import tqdm
from typing import Annotated, Any, Generator, Literal, cast

from custom_types import (
    ParserSubgraph,
    SupportedProfilerFunction,
    SupportedTaxonomiesFunction,
)

# TODO: fix this import to avoid duplicating the ApiTokenHttpxAuth declaration
#       and hardcoded API Token

# sys.path.append("..")

# from common.auth import ApiTokenHttpxAuth

TAXONOMY_NAME: SupportedTaxonomiesFunction = cast(
    SupportedTaxonomiesFunction, os.getenv("TAXONOMY_NAME", "headergen")
)
PROFILER_NAME: SupportedProfilerFunction = cast(
    SupportedProfilerFunction, os.getenv("PROFILER_NAME", "llm")
)


class ApiTokenHttpxAuth(httpx.Auth):
    """API Token Authentifier for httpx client."""

    def auth_flow(self, request: httpx.Request) -> Generator[httpx.Request, Any, None]:
        """Update the request headers to add the X-API-Token required by
        the API.

        Parameters
        ----------
        request : httpx.Request
            the request to update the headers

        Yields
        ------
        Iterator[httpx.Request]
            the updated request
        """
        request.headers["X-API-Token"] = "profil-platform-token"
        yield request


app = typer.Typer()


# Out directory

out_dir = Path("./out")
out_dir.mkdir(exist_ok=True, parents=True)


def save_result(
    json_profile: dict, original_file: Path, profile_out_dir: Path | None
) -> Path:
    """Save the json profile result to the specified output directory.

    Parameters
    ----------
    json_profile : dict
        the JSON profile to save
    original_file : Path
        the original file to retrieve the name (to store the profile with a similar name)
    profile_out_dir : Path | None
        the output directory. If None, then out_dir will be used
    """
    current_out_dir = (profile_out_dir or out_dir) / original_file.parent
    current_out_dir.mkdir(exist_ok=True, parents=True)
    result_profile_path = current_out_dir / original_file.with_suffix(".json").name
    with open(result_profile_path, "w") as f:
        json.dump(json_profile, f)
    return result_profile_path


def _cell_source_as_list(source: list[str] | str) -> list[str]:
    """Return the source cell content as a list.

    Parameters
    ----------
    source : list[str] | str
        the source cell content

    Returns
    -------
    list[str]
        the source cell content
    """
    return source if isinstance(source, list) else [source]


def read_notebook_content(notebook_path: Path) -> str:
    with open(notebook_path) as f:
        notebook_content = json.load(f)

    all_python_code: list[str] = [
        block
        for cell in notebook_content["cells"]
        if cell["cell_type"] == "code"
        for block in _cell_source_as_list(cell["source"])
    ]
    return "\n".join(all_python_code)


def read_famix_subgraphes(famix_subgraphs_path: Path) -> list[ParserSubgraph]:
    with open(famix_subgraphs_path) as f:
        raw_famix_subgraphs_content = sorted(
            json.load(f)["elements"], key=lambda sg: sg["line_start"]
        )
    return [
        ParserSubgraph(
            id=e["id"],
            library=e["library"],
            function=e["function"],
            value=e["value"],
            source=e["source"],
            step_name=e["step_name"],
        )
        for e in raw_famix_subgraphs_content
    ]


@app.command()
def profile_notebooks(
    notebook_file_or_directory: Path,
    famix_subgraphs_file_or_directory: Path,
    data_type: Annotated[str, typer.Argument()] = "ipynb",  # Literal["ipynb", "py"]
    output_directory: Annotated[Path, typer.Argument()] = None,
    verbose_mode: Annotated[bool, typer.Argument()] = False,
):
    """Profile the given notebook(s) (file or directory).
    When providing a directory, the files contained in the famix subgraphs directory
    should match *_subgraph.json to be used.

    Parameters
    ----------
    notebook_file_or_directory : Path
        the notebook file or directory to profile
    famix_subgraphs_file_or_directory : Path
        the subgraphs file or directory to use for profiling
    output_directory : Annotated[Path, typer.Argument], optional
        the optional output directory to save the profile, by default None
    verbose_mode : Annotated[bool, typer.Argument], optional
        should log additional information or not, by default False
    """
    log = print if verbose_mode else lambda *x: None

    if notebook_file_or_directory.is_dir():
        errors = {}
        all_notebooks = list(notebook_file_or_directory.rglob(f"*.{data_type}"))
        all_subgraphs = list(famix_subgraphs_file_or_directory.rglob("*_subgraph.json"))
        all_save_paths: list[Path] = []
        for notebook_file, subgraph_file in (
            pbar := tqdm(zip(all_notebooks, all_subgraphs))
        ):
            pbar.set_description(
                f"Generating profile for {str(notebook_file)[:50].ljust(50)}"
            )
            log("notebook_file=", notebook_file)
            try:
                with httpx.Client(auth=ApiTokenHttpxAuth()) as client:
                    posted_notebook_response = client.post(
                        "http://localhost:8081/profile",
                        json={
                            "notebook_file_stem": notebook_file.stem,
                            "python_content": (
                                read_notebook_content(notebook_file)
                                if data_type == "ipynb"
                                else notebook_file.read_text()
                            ),
                            "parser_elements": [
                                s.model_dump()
                                for s in read_famix_subgraphes(subgraph_file)
                            ],
                            "taxonomy_name": TAXONOMY_NAME,
                            "profiler_name": PROFILER_NAME,
                        },
                        timeout=None,
                    )
                    posted_notebook_response.raise_for_status()
                all_save_paths.append(
                    save_result(
                        posted_notebook_response.json(), notebook_file, output_directory
                    )
                )
            except Exception as e:
                errors[notebook_file.name] = str(e)
        for save_path in all_save_paths:
            print(f"Saved: {save_path}")
        if errors:
            print("ERRORS: ", errors)
    else:
        with httpx.Client(auth=ApiTokenHttpxAuth()) as client:
            posted_notebook_response = client.post(
                f"http://localhost:8081/profile",
                json={
                    "notebook_file_stem": notebook_file_or_directory.stem,
                    "python_content": (
                        read_notebook_content(notebook_file_or_directory)
                        if data_type == "ipynb"
                        else notebook_file_or_directory.read_text()
                    ),
                    "parser_elements": [
                        s.model_dump()
                        for s in read_famix_subgraphes(
                            famix_subgraphs_file_or_directory
                        )
                    ],
                    "taxonomy_name": TAXONOMY_NAME,
                    "profiler_name": PROFILER_NAME,
                },
                timeout=None,
            )
        posted_notebook_response.raise_for_status()
        save_path = save_result(
            posted_notebook_response.json(),
            notebook_file_or_directory,
            output_directory,
        )
        print(f"Saved: {save_path}")


if __name__ == "__main__":
    app()
