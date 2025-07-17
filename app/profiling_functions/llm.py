# Templating configuration

import json
import os
from jinja2 import Environment, FileSystemLoader, select_autoescape
from openai import OpenAI

from app.custom_types import ParserSubgraph
from app.profiling_functions._base import BaseMLProfiler


INFERENCE_API_URL = os.getenv("INFERENCE_API_URL", "profil_ollama:11434")
MODEL_ID = os.getenv(
    "MODEL_ID", "qwen2.5-coder:7b"
)  # qwen/qwen2.5-coder-7b-instruct for LMS

env = Environment(
    loader=FileSystemLoader("./templates"), autoescape=select_autoescape()
)


class LLMProfiler(BaseMLProfiler):

    def __init__(self, python_content: str, taxonomy_name: str):
        super().__init__(python_content, taxonomy_name)

        # loading the LLM system and user prompt templates
        system_prompt_template = env.get_template(
            f"system_prompt_{taxonomy_name}_taxonomy.jinja"
        )
        self.user_prompt_template = env.get_template("user_prompt.jinja")

        # loading the LLM classification response schema
        classification_response_schema_template = env.get_template(
            "classification_response_schema.jinja"
        )
        self.classification_response_schema = (
            classification_response_schema_template.render(
                steps_taxonomy=self.steps_taxonomy
            )
        )
        self.system_prompt_content = system_prompt_template.render(
            steps_taxonomy=self.steps_taxonomy, all_python_code=python_content
        )

        # LLM client

        self.client = OpenAI(
            base_url=f"http://{INFERENCE_API_URL}/v1", api_key="inference-key"
        )

    def profile_subgraph(self, subgraph: ParserSubgraph, default_step: str) -> str:
        user_prompt_content = self.user_prompt_template.render(
            python_code_line=subgraph.source
        )

        # see https://cookbook.openai.com/examples/multiclass_classification_for_transactions
        completion = self.client.chat.completions.create(
            model=MODEL_ID,
            messages=[
                {
                    "role": "system",
                    "content": self.system_prompt_content,
                },
                {"role": "user", "content": user_prompt_content},
            ],
            response_format=json.loads(self.classification_response_schema),
            temperature=0,
            # top_p=1,
            # frequency_penalty=0,
            # presence_penalty=0
        )

        classified_line = json.loads(completion.choices[0].message.content)
        return (
            classified_line["class"]
            if classified_line["class"] in self.steps_taxonomy
            else default_step
        )
