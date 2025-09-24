# Templating configuration

import json
import os

import numpy as np

from jinja2 import Environment, FileSystemLoader, select_autoescape

try:
    # trying monitored by default
    from langfuse.openai import OpenAI
except:
    from openai import OpenAI

from app.custom_types import ParserSubgraph, SupportedTaxonomiesFunction
from app.profiling_functions._base import BaseMLProfiler


INFERENCE_API_URL = os.getenv("INFERENCE_API_URL", "profil_vllm:11434")
MODEL_ID = os.getenv("MODEL_ID", "qwen2.5-coder:7b")

env = Environment(
    loader=FileSystemLoader("./templates"), autoescape=select_autoescape()
)


class LLMProfiler(BaseMLProfiler):

    def __init__(self, python_content: str, taxonomy_name: SupportedTaxonomiesFunction):
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
            all_python_code=python_content
        )

        # LLM client

        self.client = OpenAI(
            base_url=f"http://{INFERENCE_API_URL}/v1", api_key="inference-key"
        )

    def profile_subgraph(
        self, subgraph: ParserSubgraph, default_step: str
    ) -> tuple[str, float | None, list[tuple[str, float]]]:
        user_prompt_content = self.user_prompt_template.render(
            steps_taxonomy=self.steps_taxonomy, python_code_line=subgraph.source
        )

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
            extra_body={
                "chat_template_kwargs": {"enable_thinking": False},
            },
            # see https://cookbook.openai.com/examples/multiclass_classification_for_transactions
            temperature=0,
            max_tokens=15,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
            # see https://cookbook.openai.com/examples/using_logprobs
            logprobs=True,
            top_logprobs=len(self.steps_taxonomy),
        )

        logprobs_content = completion.choices[0].logprobs.content
        all_linear_probs = [
            (logprob.token, np.round(np.exp(logprob.logprob) * 100, 2))
            for logprob in logprobs_content[0].top_logprobs
        ]
        perplexity_score = np.exp(
            -np.mean([token.logprob for token in logprobs_content])
        )

        completion_content = completion.choices[0].message.content

        if not completion_content:
            return default_step, -1, []

        classified_line = json.loads(completion_content)
        return (
            (
                classified_line["class"]
                if classified_line["class"] in self.steps_taxonomy
                else default_step
            ),
            perplexity_score,
            all_linear_probs,
        )
