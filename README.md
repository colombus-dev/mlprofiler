# profil-platform-poc - LLM

TODO

## Requirements

In addition to the root project, the LLM sub-project has the following requirements:

* LM studio (https://lmstudio.ai/) and the lms CLI (https://lmstudio.ai/docs/cli)

## How to use it

### Install dependencies

```bash
$ poetry install --with llm
```

### Start the LM Studio server

*Note: Depending on your system, you may need to start the LM Studio application before being able to start the lms server*

```bash
$ ./scripts/start_lms_server.sh
```

### Run the CLI

```bash
$ poetry run python src/main.py data/ data/
```
