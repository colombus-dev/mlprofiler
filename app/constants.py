import os

APP_VERSION = "0.3.0"

# TODO ymu: Replace with Pydantic config
INFERENCE_API_URL_PREFIX = os.environ["LLM_INFERENCE_API_URL"]
PARSER_API_URL_PREFIX = os.environ["PARSER_API_URL_PREFIX"]
