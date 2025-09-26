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
    from openai.types.chat import ChatCompletion

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
        system_prompt_template = env.get_template("system_prompt.jinja")
        self.user_prompt_template = env.get_template(
            f"user_prompt_{taxonomy_name}_taxonomy.jinja"
        )

        # loading the LLM classification response schema
        classification_response_schema_template = env.get_template(
            "classification_response_schema.jinja"
        )
        self.classification_response_schema = (
            classification_response_schema_template.render(
                compatible_step_names=self.taxonomy.get_compatible_steps_names()
            )
        )
        self.system_prompt_content = system_prompt_template.render(
            all_python_code=python_content
        )

        # LLM client

        self.client: OpenAI = OpenAI(
            base_url=f"http://{INFERENCE_API_URL}/v1", api_key="inference-key"
        )

    def profile_subgraph(
        self, subgraph: ParserSubgraph, default_step: str
    ) -> tuple[str, float | None, list[list[tuple[str, float]]]]:
        user_prompt_content = self.user_prompt_template.render(
            taxonomy=self.taxonomy,
            python_code_line=subgraph.source,
            subgraph_library=subgraph.library,
            subgraph_function=subgraph.function,
        )

        completion: ChatCompletion = self.client.chat.completions.create(
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
                # "guided_choice": self.taxonomy.compatible_steps_names,
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
            top_logprobs=len(self.taxonomy.get_compatible_steps_names()),
        )

        completion_content = completion.choices[0].message.content

        if not completion_content:
            return default_step, -1, []

        classified_line = json.loads(completion_content)
        predicted_class = classified_line["class"]

        # excluding json structured output specific tokens to avoid biasing probs
        # and perplexity score (as the linear probs of these tokens are most of the
        # time close to 100) leading to a low perplexity score
        relevant_top_logprobs = [
            logprob_content.top_logprobs
            for logprob_content in completion.choices[0].logprobs.content
            if logprob_content.top_logprobs[0].token
            and logprob_content.top_logprobs[0].token in predicted_class
        ]
        relevant_content_logprobs = [
            token.logprob
            for token in completion.choices[0].logprobs.content
            if token.token and token.token in predicted_class
        ]

        # converting all logprobs to linear probabilities
        all_linear_probs = [
            [
                linear_prob
                for linear_prob in next_token_linear_probs
                # filtering out linear prob equal to 0 as they represent noise
                if linear_prob[1] > 0
            ]
            for next_token_linear_probs in [
                [
                    (logprob.token, np.round(np.exp(logprob.logprob) * 100, 2))
                    for logprob in top_logprob
                ]
                for top_logprob in relevant_top_logprobs
            ]
        ]

        # we compute the perplexity_score (excluding the json structured output specific tokens to avoid biases)
        perplexity_score = np.exp(
            -np.mean([logprob for logprob in relevant_content_logprobs])
        )

        return (
            self.taxonomy.get_original_name_from_compatible(
                predicted_class, default_step
            ),
            perplexity_score,
            all_linear_probs,
        )
