# profil-platform-poc - LLM

The LLM module defines the CLI and API used to compute profiles using an LLM inference server.

This module does not detail the inference server deployment. Check the corresponding [docker-compose.yml](../docker-compose.yml) file for more details about the inference server.

## Requirements

Additionaly to the root project's requirements:

* The **inference server** reachable at the address defined by the **INFERENCE_API_URL** environment variable.
* The loaded **LLM model** defined by the **MODEL_ID** environment variable.

## How to use it

### Install dependencies

```bash
$ poetry install --with llm
```

### Load the LLM model

```bash
$ MODEL_ID=qwen2.5-coder:7b ./scripts/init_ollama.sh
```

### Run the CLI

```bash
$ poetry run python src/cli.py data/ data/
```
