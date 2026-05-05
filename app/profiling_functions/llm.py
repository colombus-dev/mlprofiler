from typing import Any
import json

import numpy as np
from jinja2 import Environment, FileSystemLoader, select_autoescape

try:
    # trying monitored by default
    from langfuse import get_client, propagate_attributes
    from langfuse.openai import AsyncOpenAI

    langfuse = get_client()
except ValueError:
    from contextlib import contextmanager

    from openai import AsyncOpenAI


    def propagate_attributes(*args, **kwargs):
        ...


    class LangfuseMock:
        @contextmanager
        def start_as_current_observation(self, *args, **kwargs):
            ...


    langfuse = LangfuseMock()

from openai.types.chat import ChatCompletion

from app.constants import INFERENCE_API_URL_PREFIX
from app.models.parser import ParserSubgraph
from app.models.profiler import ProfileResult
from app.profiling_functions.base import BaseMLProfiler, Taxonomy

env = Environment(
    loader=FileSystemLoader("./templates"), autoescape=select_autoescape()
)


class InferenceClientSingleton:
    _INSTANCE_BY_NAME: dict[str, dict[str, Any]] = {}

    @classmethod
    async def get_instance(cls, name: str) -> tuple[AsyncOpenAI, str]:
        instance = cls._INSTANCE_BY_NAME.get(name)
        if instance is None:
            client = AsyncOpenAI(
                base_url=f"{name}", api_key="inference-key"
            )
            cls._INSTANCE_BY_NAME[name] = {
                'client': client,
                'model_id': (await client.models.list()).data[0].id,
            }
            instance = cls._INSTANCE_BY_NAME[name]
        return instance['client'], instance['model_id']


class LLMProfiler(BaseMLProfiler):
    def __init__(self, source_code: str, taxonomy: Taxonomy):
        super().__init__(source_code, taxonomy)

        # loading the LLM system and user prompt templates
        self._system_prompt_template = env.get_template("system_prompt.jinja")
        self._user_prompt_template = env.get_template("user_prompt_taxonomy.jinja")

        # loading the LLM classification response schema
        classification_response_schema_template = env.get_template(
            "classification_response_schema.jinja"
        )
        self.__classification_response_schema = (
            classification_response_schema_template.render(
                compatible_step_names=self.taxonomy.get_steps_names()
            )
        )

    async def profile_subgraph(self, subgraph: ParserSubgraph) -> ProfileResult:
        context_source_code = self.compute_source_code_context(target_line=subgraph.line.start)
        system_prompt_content = self._system_prompt_template.render(
            all_python_code=context_source_code
        )
        user_prompt_content = self._user_prompt_template.render(
            taxonomy=self.taxonomy,
            python_code_line=subgraph.source,
            expected_class=None,
            is_multi_class=False
        )
        client, model_id = await InferenceClientSingleton.get_instance(INFERENCE_API_URL_PREFIX)
        with langfuse.start_as_current_observation(as_type="span", name="OpenAI-generation"):
            # Propagate session_id to all observations including OpenAI generation
            with propagate_attributes(session_id=self.session_id):
                completion: ChatCompletion = await client.chat.completions.create(
                    model=model_id,
                    messages=[
                        {
                            "role": "system",
                            "content": system_prompt_content,
                        },
                        {
                            "role": "user",
                            "content": user_prompt_content
                        },
                    ],
                    response_format=json.loads(self.__classification_response_schema),
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
                    top_logprobs=len(self.taxonomy.get_steps_names()),
                )

                completion_content = completion.choices[0].message.content

        if not completion_content:
            return ProfileResult(step=self.taxonomy.default_step, perplexity=-1)

        try:
            classified_line = json.loads(completion_content)
            predicted_class = classified_line["class"]
        except (json.JSONDecodeError, TypeError):
            print("Bad format response")
            return ProfileResult(step=self.taxonomy.default_step, perplexity=-1)

        # excluding json structured output specific tokens to avoid biasing probs
        # and perplexity score (as the linear probs of these tokens are most of the
        # time close to 100) leading to a low perplexity score
        """
        relevant_top_logprobs = [
            logprob_content.top_logprobs
            for logprob_content in completion.choices[0].logprobs.content
            if logprob_content.top_logprobs[0].token
               and logprob_content.top_logprobs[0].token in predicted_class
        ]
        """
        relevant_content_logprobs = [
            token.logprob
            for token in completion.choices[0].logprobs.content
            if token.token and token.token in predicted_class
        ]

        # converting all logprobs to linear probabilities
        """
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
        """

        # we compute the perplexity_score (excluding the json structured output specific tokens to avoid biases)
        perplexity_score = np.exp(
            -np.mean([logprob for logprob in relevant_content_logprobs])
        )

        retrieved_step = (
            predicted_class
            if predicted_class in self.taxonomy.get_steps_names()
            else self.taxonomy.default_step
        )
        return ProfileResult(step=retrieved_step, perplexity=perplexity_score)
