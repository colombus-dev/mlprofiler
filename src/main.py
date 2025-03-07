from pathlib import Path
from typing import Annotated

import typer

from tqdm import tqdm

from utils import profile_notebook_file, save_result


app = typer.Typer()


@app.command()
def profile_notebooks(
    notebook_file_or_directory: Path,
    famix_subgraphs_file_or_directory: Path,
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
        report = {}
        errors = {}
        all_notebooks = list(notebook_file_or_directory.rglob("*.ipynb"))
        all_subgraphs = list(famix_subgraphs_file_or_directory.rglob("*_subgraph.json"))
        for notebook_file, subgraph_file in (pbar := tqdm(zip(all_notebooks, all_subgraphs))):
            pbar.set_description(
                f"Generating profile for {str(notebook_file)[:50].ljust(50)}"
            )
            log("notebook_file=", notebook_file)
            try:
                res = profile_notebook_file(notebook_file, subgraph_file)
                save_result(res, notebook_file, output_directory)
            except Exception as e:
                errors[notebook_file.name] = str(e)
        if errors:
            print("ERRORS: ", errors)
    else:
        res = profile_notebook_file(notebook_file_or_directory, famix_subgraphs_file_or_directory)
        save_result(res, notebook_file_or_directory, output_directory)


if __name__ == "__main__":
    app()
