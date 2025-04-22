from .utils import ParserElement, profile_python_content

from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class LLMResult(BaseModel):
    parser_element_id: str
    step_name: str
    algo_name: str
    algo_family: str


class ProfileNotebookParams(BaseModel):
    notebook_file_stem: str
    python_content: str
    parser_elements: list[ParserElement]


class ProfileNotebookResponse(BaseModel):
    llm_profile: list[ParserElement]


@app.post("/profile")
def profile_notebook(params: ProfileNotebookParams) -> list[Any]:
    """Mock the given notebook (LLM-like) profiling.

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
    result_profile = profile_python_content(
        params.python_content, params.parser_elements
    )

    res: list[LLMResult] = []
    i = 0
    for step in result_profile:
        for t in step["tasks"]:
            res.append(
                LLMResult(
                    parser_element_id=params.parser_elements[i].id,
                    step_name=step["name"],
                    algo_name=t["algoName"],
                    algo_family=t["algoFamily"],
                )
            )
            i += 1

    return res


if __name__ == "__main__":
    app()
