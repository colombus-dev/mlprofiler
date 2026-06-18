from functools import lru_cache
from typing import Any, Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')

    app_version: str = "0.3.0"

    langfuse_public_key: str = Field(default="")
    langfuse_secret_key: str = Field(default="")
    langfuse_base_url: str = Field(default="")
    langfuse_flush_at: int = Field(default=1)

    parser_api_url_prefix: str = Field(default="")

    inference_mode: Literal["dmr", "vllm"] = Field(default="dmr")
    vllm_inference_api_url_prefix: str = Field(default="")
    dmr_inference_api_url: str = Field(default="")

    langfuse_client: Any = None
    langfuse_propagate_attributes: Any = None
    openai_client_class: Any = None

    @property
    def inference_api_url_prefix(self):
        if self.inference_mode == "dmr":
            return self.dmr_inference_api_url
        elif self.inference_mode == "vllm":
            return self.vllm_inference_api_url_prefix
        else:
            raise NotImplementedError(f'{self.inference_mode} inference mode not implemented')

    def is_langfuse_enabled(self):
        return bool(self.langfuse_base_url)

    def build_langfuse_client(self):
        if self.is_langfuse_enabled():
            from langfuse import get_client, propagate_attributes
            from langfuse.openai import AsyncOpenAI
            self.langfuse_client = get_client()
            self.langfuse_propagate_attributes = propagate_attributes
            self.openai_client_class = AsyncOpenAI
        else:
            from contextlib import contextmanager

            from openai import AsyncOpenAI

            @contextmanager
            def propagate_attributes(*args, **kwargs):
                yield

            class LangfuseMock:
                @contextmanager
                def start_as_current_observation(self, *args, **kwargs):
                    yield

            self.langfuse_client = LangfuseMock()
            self.langfuse_propagate_attributes = propagate_attributes
            self.openai_client_class = AsyncOpenAI


@lru_cache()
def get_settings() -> Settings:
    settings = Settings()
    settings.build_langfuse_client()
    return settings
