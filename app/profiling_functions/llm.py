# Templating configuration

import json
import os

import numpy as np

from jinja2 import Environment, FileSystemLoader, select_autoescape

try:
    # trying monitored by default
    from langfuse import get_client, propagate_attributes
    from langfuse.openai import AsyncOpenAI

    langfuse = get_client()
except:
    from openai import AsyncOpenAI

    def propagate_attributes(*args, **kwargs): ...

    class LangfuseMock:
        def __enter__(self): ...
        def __exit__(self): ...
        def start_as_current_observation(self, *args, **kwargs): ...

    langfuse = LangfuseMock()


from openai.types.chat import ChatCompletion

from app.custom_types import ParserSubgraph
from app.profiling_functions._base import BaseMLProfiler, Taxonomy


INFERENCE_API_URL = os.getenv("INFERENCE_API_URL", "mlprofiler_vllm:11434")

env = Environment(
    loader=FileSystemLoader("./templates"), autoescape=select_autoescape()
)


class InferenceClientSingleton:
    __INSTANCE: AsyncOpenAI | None = None
    __INSTANCE_NAME: str = ""
    __MODEL_ID: str = ""

    @classmethod
    async def get_instance(cls, instance_name: str) -> tuple[AsyncOpenAI, str]:
        if cls.__INSTANCE and cls.__INSTANCE_NAME == instance_name:
            return cls.__INSTANCE, cls.__MODEL_ID
        cls.__INSTANCE_NAME = instance_name
        cls.__INSTANCE = AsyncOpenAI(
            base_url=f"http://{INFERENCE_API_URL}/v1", api_key="inference-key"
        )
        cls.__MODEL_ID = (await cls.__INSTANCE.models.list()).data[0].id
        return cls.__INSTANCE, cls.__MODEL_ID


class LLMProfiler(BaseMLProfiler):
    def __init__(self, python_content: str, taxonomy: Taxonomy):
        super().__init__(python_content, taxonomy)

        # loading the LLM system and user prompt templates
        self.__system_prompt_template = env.get_template("system_prompt.jinja")
        self.__user_prompt_template = env.get_template("user_prompt_taxonomy.jinja")

        # loading the LLM classification response schema
        classification_response_schema_template = env.get_template(
            "classification_response_schema.jinja"
        )
        self.__classification_response_schema = (
            classification_response_schema_template.render(
                compatible_step_names=self.taxonomy.get_steps_names()
            )
        )
        self.__system_prompt_content = self.__system_prompt_template.render(
            all_python_code=self._python_content
        )

    @BaseMLProfiler.python_content.setter
    def python_content(self, new_content):
        self._python_content = new_content
        self.__system_prompt_content = self.__system_prompt_template.render(
            all_python_code=self._python_content
        )

    async def profile_subgraph(
        self,
        subgraph: ParserSubgraph,
        default_step: str,
        expected: str | list[str] | None = None,
    ) -> tuple[str, float | None, list[list[tuple[str, float]]]]:
        if self.__system_prompt_content:
            user_prompt_content = self.__user_prompt_template.render(
                taxonomy=self.taxonomy,
                python_code_line=subgraph.source,
                expected_class=expected,
                is_multi_class=isinstance(expected, list),
            )
        else:
            # if no system prompt content, we pass it to the user prompt
            # as the model may not support system messages (e.g., magicoder)
            user_prompt_content = self.__user_prompt_template.render(
                taxonomy=self.taxonomy,
                python_code_line=subgraph.source,
                expected_class=expected,
                is_multi_class=isinstance(expected, list),
                all_python_code=self._python_content,
            )

        client, model_id = await InferenceClientSingleton.get_instance(
            "http://{INFERENCE_API_URL}/v1"
        )
        with langfuse.start_as_current_observation(
            as_type="span", name="OpenAI-generation"
        ):
            # Propagate session_id to all observations including OpenAI generation
            with propagate_attributes(session_id=self.session_id):
                completion: ChatCompletion = await client.chat.completions.create(
                    model=model_id,
                    messages=[
                        {
                            "role": "system",
                            "content": self.__system_prompt_content,
                        },
                        {"role": "user", "content": user_prompt_content},
                    ]
                    if self.__system_prompt_content
                    else [{"role": "user", "content": user_prompt_content}],
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
            return default_step, -1, []

        try:
            classified_line = json.loads(completion_content)
            predicted_class = classified_line["class"]
        except:
            print("Bad format response")
            return default_step, -1, []

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

        retrieved_step = (
            predicted_class
            if predicted_class in self.taxonomy.get_steps_names()
            else default_step
        )
        return (
            retrieved_step,
            perplexity_score,
            all_linear_probs,
        )
