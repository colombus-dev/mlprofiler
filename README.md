# mlprofiler - The ML pipelines profiler

## Requirements

* Docker (tested on version 28.5.1, build e180ab8)
* Docker Compose (tested on version v2.40.0)
* [Docker Model Runner](https://docs.docker.com/ai/model-runner/get-started/#docker-engine) (tested on version v1.1.37)

## Deployment

The following docker compose commands deploy the mlprofiler API and vLLM instance:

```bash
$ cd docker
$ docker compose --env-file .env build
$ docker compose --env-file .env up
```

It is also possible to deploy the LLM monitoring platform [Langfuse](https://langfuse.com/docs)
or [Grafana](https://github.com/vllm-project/vllm/tree/main/examples/online_serving/prometheus_grafana#prometheus-and-grafana) as follows:

```bash
$ cd docker
$ docker compose --file docker-compose-monitor-langfuse.yml up
$ docker compose --file docker-compose-monitor-grafana.yml up
```

## Troubleshooting

### Got permission denied while trying to connect to the Docker daemon socket at unix:///var/run/docker.sock

Allow your user to use the socket:
```bash
sudo usermod -a -G docker $USER
newgrp docker
reboot
```

### Failed to solve: process "/bin/sh -c uv sync --locked --no-install-project" did not complete successfully: exit code: 1

Regenerate the lock file by executing:
```bash
uv lock
```

### Network colombus-dev_network declared as external, but could not be found

Create the missing network:
```bash
docker network create "colombus-dev_network"
```

### Error response from daemon: could not select device driver "nvidia" with capabilities: [[gpu]]

Install the nvidia toolkit
https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html#with-apt-ubuntu-debian

Configure Docker to use the NVIDIA runtime
https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html#configuring-docker

Verify GPU is accessible inside Docker
https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/sample-workload.html
