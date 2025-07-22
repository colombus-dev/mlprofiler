# profil-platform-poc - LLM

The LLM module defines the CLI and API used to compute profiles using an LLM inference server.

This module does not detail the inference server deployment. Check the corresponding [README.md](../README.md) and [docker-compose.yml](../docker-compose.yml) files for more details about the inference server and its deployment.

## Requirements

Additionaly to the root project's requirements:

* The **inference server** reachable at the address defined by the **INFERENCE_API_URL** environment variable.
* The loaded **LLM model** defined by the **MODEL_ID** environment variable.

## How to use it

### Build the docker image

*Note: Currently, it is required to build the llm API docker image at the root of the project. This will be changed in the future to ease image building.*

The following command build the llm API docker image:

```bash
$ cd ..  # if your bash session is located in the llm/ directory
$ docker build --platform linux/amd64 -f llm/Dockerfile --tag mlprofile:llm_api-v0.1 .
$ cd -   # if your bash session was located in the llm/ directory
```

If you want to use a local LLM inference server. Start the inference server:

```bash
./scripts/start_lms_server.sh
```

### Load the LLM model

```bash
$ MODEL_ID=qwen2.5-coder:7b ./scripts/init_ollama.sh
```

### Profile a notebook

#### Using the API (legacy)

*Note: See http://localhost:8081/docs#/default/profile_notebook_profile_post for more information.*

```curl
$ curl 'http://localhost:8081/profile' \
    -H 'Content-Type: application/json' \
    --data-raw $'{...}'
```

#### Using the CLI (recommended)

##### Ollama

```bash
$ docker run --platform linux/amd64 \
    --network profil-platform-poc_default \
    -e INFERENCE_API_URL=profil_ollama:11434 \
    -v ./data:/code/data \
    -v ./resources:/code/resources \
    -v ./out:/code/out \
    mlprofile:llm_api-v0.1 python app/cli.py data/corpus_students/student_0.ipynb data/corpus_students/student_0_subgraph.json
```

##### LMStudio

```bash
docker run --platform linux/amd64 \
    --network profil-platform-poc_default \
    -e INFERENCE_API_URL=host.docker.internal:1234 \
    -e MODEL_ID=qwen/qwen2.5-coder-7b-instruct \
    -v ./data:/code/data \
    -v ./resources:/code/resources \
    -v ./out:/code/out \
    mlprofile:llm_api-v0.1 python app/cli.py data/corpus_students/student_0.ipynb data/corpus_students/student_0_subgraph.json
```