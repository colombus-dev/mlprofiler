import json

from pathlib import Path

from tqdm import tqdm
from jinja2 import Environment, FileSystemLoader, select_autoescape
from openai import OpenAI

# Out directory

out_dir = Path("./out")
out_dir.mkdir(exist_ok=True, parents=True)

# Templating configuration

env = Environment(
    loader=FileSystemLoader("../llm/templates"), autoescape=select_autoescape()
)

system_prompt_template = env.get_template("system_prompt.jinja")
user_prompt_template = env.get_template("user_prompt.jinja")
classification_response_schema_template = env.get_template(
    "classification_response_schema.jinja"
)

# loading the stages/steps
# source: https://github.com/secure-software-engineering/HeaderGen/blob/1ea52265ca4e76bb202a2deb26f3b9394d3caa95/framework_models/__init__.py#L28
with open("resources/phases_groups.json") as f:
    stages_steps_taxonomy = json.load(f)
    steps_taxonomy = [v for s in stages_steps_taxonomy.values() for v in s]

# loading the LLM classification response schema
classification_response_schema = classification_response_schema_template.render(
    steps_taxonomy=steps_taxonomy
)

# LLM client

client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")


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


def _retrieve_stage_for_step(
    stages_steps_taxonomy: dict[str, str], step: str
) -> str | None:
    """Retrieve the stage corresponding to the given step.

    Parameters
    ----------
    stages_steps_taxonomy : dict[str, str]
        the stages-to-steps taxonomy
    step : str
        the step to retrieve the corresponding stage

    Returns
    -------
    str | None
        the stage if found
    """
    for k, v in stages_steps_taxonomy.items():
        if step in v:
            return k


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
    json_profile = []
    prev_step = None
    prev_stage = None

    with open(notebook_path) as f:
        notebook_content = json.load(f)
    with open(famix_subgraphs_path) as f:
        famix_subgraphs_content = json.load(f)

    all_python_code = [
        block
        for cell in notebook_content["cells"]
        if cell["cell_type"] == "code"
        for block in _cell_source_as_list(cell["source"])
    ]

    system_prompt_content = system_prompt_template.render(
        steps_taxonomy=steps_taxonomy, all_python_code=all_python_code
    )

    for subgraph in (pbar := tqdm(famix_subgraphs_content)):
        line = subgraph["source"]
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

        res = {
            "algoFamily": classified_line["algorithm_family"],
            "algoName": classified_line["algorithm_name"],
            "library": subgraph["library"],
            "function": subgraph["function"],
            "tasks": [{"name": line, "tasks": []}],
        }
        current_step = (
            classified_line["class"]
            if classified_line["class"] in steps_taxonomy
            else "Others"
        )
        current_stage = _retrieve_stage_for_step(stages_steps_taxonomy, current_step)

        if prev_stage == current_stage:
            if prev_step == current_step:
                json_profile[-1]["tasks"][-1]["tasks"].append(res)
            else:
                json_profile[-1]["tasks"].append({"name": current_step, "tasks": [res]})
        else:
            json_profile.append(
                {
                    "name": current_stage,
                    "tasks": [{"name": current_step, "tasks": [res]}],
                }
            )
        prev_stage = current_stage
        prev_step = current_step

    return json_profile
