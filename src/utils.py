import json
import os

from pathlib import Path
from typing import Any

from pydantic import BaseModel
from tqdm import tqdm
from jinja2 import Environment, FileSystemLoader, select_autoescape
from openai import OpenAI


LMSTUDIO_API_URL = os.getenv("LMSTUDIO_API_URL", "localhost:1234")


class ParserElement(BaseModel):
    # TODO: move this to common and use it in mock and core
    id: str
    library: str
    function: str
    value: dict[str, Any]
    source: str
    step_name: str


# Out directory

out_dir = Path("./out")
out_dir.mkdir(exist_ok=True, parents=True)

# Templating configuration

env = Environment(
    loader=FileSystemLoader("./templates"), autoescape=select_autoescape()
)

system_prompt_template = env.get_template("system_prompt.jinja")
user_prompt_template = env.get_template("user_prompt.jinja")
classification_response_schema_template = env.get_template(
    "classification_response_schema.jinja"
)

algorithms_system_prompt_template = env.get_template("algorithms/system_prompt.jinja")
algorithms_user_prompt_template = env.get_template("algorithms/user_prompt.jinja")
algorithms_classification_response_schema_template = env.get_template(
    "algorithms/classification_response_schema.jinja"
)

with open("resources/algorithms.json") as f:
    available_algorithms = json.load(f)

# loading the stages/steps
# source: https://github.com/secure-software-engineering/HeaderGen/blob/1ea52265ca4e76bb202a2deb26f3b9394d3caa95/framework_models/__init__.py#L28
with open("resources/phases_groups.json") as f:
    stages_steps_taxonomy = json.load(f)
    steps_taxonomy = [v for s in stages_steps_taxonomy.values() for v in s]

# loading the LLM classification response schema
classification_response_schema = classification_response_schema_template.render(
    steps_taxonomy=steps_taxonomy
)
algorithms_classification_response_schema = (
    algorithms_classification_response_schema_template.render()
)

# LLM client

client = OpenAI(base_url=f"http://{LMSTUDIO_API_URL}/v1", api_key="lm-studio")


def _cell_source_as_list(source: list[str] | str):
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


def save_result(json_profile: dict, original_file: Path, profile_out_dir: Path | None):
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
    with open(current_out_dir / original_file.with_suffix(".json").name, "w") as f:
        json.dump(json_profile, f)


def profile_python_content(python_content: str, famix_subgraphes: list[ParserElement]):
    json_profile = []
    prev_step = None

    system_prompt_content = system_prompt_template.render(
        steps_taxonomy=steps_taxonomy, all_python_code=python_content
    )
    algorithms_system_prompt_content = algorithms_system_prompt_template.render(
        algorithm_families_taxonomy=available_algorithms["algoFamilies"],
        algorithm_names_taxonomy=available_algorithms["algoNames"],
        all_python_code=python_content,
    )

    for subgraph in (pbar := tqdm(famix_subgraphes)):
        line = subgraph.source
        pbar.set_description(f"Classifying line: {line[:50].ljust(50).strip()}")

        user_prompt_content = user_prompt_template.render(python_code_line=line)
        completion = client.chat.completions.create(
            model="qwen/qwen2.5-coder-7b-instruct",
            messages=[
                {
                    "role": "system",
                    "content": system_prompt_content,
                },
                {"role": "user", "content": user_prompt_content},
            ],
            response_format=json.loads(classification_response_schema),
            temperature=0,  # 0 for ~ determinism
        )

        classified_line = json.loads(completion.choices[0].message.content)

        algorithms_user_prompt_content = algorithms_user_prompt_template.render(
            python_code_line=line
        )
        algorithms_completion = client.chat.completions.create(
            model="qwen/qwen2.5-coder-7b-instruct",
            messages=[
                {
                    "role": "system",
                    "content": algorithms_system_prompt_content,
                },
                {"role": "user", "content": algorithms_user_prompt_content},
            ],
            response_format=json.loads(algorithms_classification_response_schema),
            temperature=0,  # 0 for ~ determinism
        )

        algorithms_classified_line = json.loads(
            algorithms_completion.choices[0].message.content
        )

        res = {
            "id": subgraph.id,
            "algoFamily": algorithms_classified_line["algorithm_family"],
            "algoName": algorithms_classified_line["algorithm_name"],
            "library": subgraph.library,
            "function": subgraph.function,
            "tasks": [{"name": line, "tasks": []}],
        }

        if (
            algorithms_classified_line["algorithm_family"]
            not in available_algorithms["algoFamilies"]
        ):
            available_algorithms["algoFamilies"].append(
                algorithms_classified_line["algorithm_family"]
            )
        if (
            algorithms_classified_line["algorithm_name"]
            not in available_algorithms["algoNames"]
        ):
            available_algorithms["algoNames"].append(
                algorithms_classified_line["algorithm_name"]
            )

        with open("resources/algorithms.json", "w") as f:
            json.dump(available_algorithms, f, indent=4)

        current_step = (
            classified_line["class"]
            if classified_line["class"] in steps_taxonomy
            else "Others"
        )
        if (
            current_step == "Library Loading"
            and subgraph.step_name != "Library Loading"
        ):
            current_step = "Others"
        if subgraph.step_name == "Library Loading":
            current_step = "Library Loading"

        if prev_step == current_step:
            json_profile[-1]["tasks"].append(res)
        else:
            json_profile.append(
                {
                    "name": current_step,
                    "tasks": [res],
                }
            )

        prev_step = current_step

    return json_profile


def profile_notebook_file(notebook_path: Path, famix_subgraphs_path: Path):
    """Profile the given notebook file.

    Parameters
    ----------
    notebook_path : Path
        the notebook file path
    famix_subgraphs_path : Path
        the famix subgraphs file path
    famix_subgraphs : list[dict]
        the famix subgraphs corresponding to the given file
    """
    with open(notebook_path) as f:
        notebook_content = json.load(f)
    with open(famix_subgraphs_path) as f:
        raw_famix_subgraphs_content = sorted(
            json.load(f)["elements"], key=lambda sg: sg["line_start"]
        )
        famix_subgraphs_content = [
            ParserElement(
                id=e["id"],
                library=e["library"],
                function=e["function"],
                value=e["value"],
                source=e["source"],
                step_name=e["step_name"],
            )
            for e in raw_famix_subgraphs_content
        ]

    all_python_code = [
        block
        for cell in notebook_content["cells"]
        if cell["cell_type"] == "code"
        for block in _cell_source_as_list(cell["source"])
    ]

    return profile_python_content(all_python_code, famix_subgraphs_content)
