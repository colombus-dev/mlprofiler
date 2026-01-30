# mlprofiler - The ML pipelines profiler

## Requirements

* Docker (tested on version 28.5.1, build e180ab8)
* Docker Compose (tested on version v2.40.0)

## Deployment

The following docker compose commands deploy the mlprofiler API and vLLM instance:

```bash
$ docker compose --env-file .env build
$ docker compose --env-file .env up
```

It is also possible to deploy the LLM monitoring platform (Langfuse) as follows:

```bash
$ docker compose --file docker-compose-monitor-local.yml up
```
