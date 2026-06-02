import os

APP_VERSION = "0.3.0"

# TODO ymu: Replace with Pydantic config
VLLM_FORCE = int(os.environ["VLLM_FORCE"])
if VLLM_FORCE:
    INFERENCE_API_URL_PREFIX = os.environ["vLLM_INFERENCE_API_URL_PREFIX"]
    print(f'found VLLM_FORCE={VLLM_FORCE} using VLLM url={INFERENCE_API_URL_PREFIX}')
else:
    INFERENCE_API_URL_PREFIX = os.environ["LLM_INFERENCE_API_URL"]
    print(f'found VLLM_FORCE={VLLM_FORCE} using DMR url={INFERENCE_API_URL_PREFIX}')
PARSER_API_URL_PREFIX = os.environ["VESPUCCI_PARSER_API_URL_PREFIX"]
