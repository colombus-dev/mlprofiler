# profil-platform-poc - LLM

The LLM module defines the CLI and API used to compute profiles using an LLM inference server.

This module does not detail the inference server deployment. Check the corresponding [README.md](../README.md) and [docker-compose.yml](../docker-compose.yml) files for more details about the inference server and its deployment.

## Requirements

Additionaly to the root project's requirements:

* The platform deployed with at least the llm_api service.
* (Optional) The **inference server** reachable at the address defined by the **INFERENCE_API_URL** environment variable.

## How to use it

*Note: Make sure the platform is deployed and the llm_api service is ready.*

### Profile a notebook

#### Using the API

*Note: See http://localhost:8081/docs#/default/profile_notebook_profile_post for more information.*

```curl
$ curl 'http://localhost:8081/profile' \
    -H 'Content-Type: application/json' \
    --data-raw $'{...}'
```

#### Using the CLI

*Note: You can configure the taxonomy and "profiler" used to compute the ML profile by editing the [.env](.env) file.*

The following command computes the ML profile of the provided notebook (or directory of notebooks) and subgraphes (or directory of subgraphes) by sending queries to the API:

```bash
$ docker exec --env-file .env profil-platform-poc-llm_api-1 python app/cli.py data/corpus_students/student_0.ipynb data/corpus_students/student_0_subgraph.json
```

The result profile will be saved in the [out/](./out/) directory.
