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
$ docker compose --file docker-compose-monitor-local.yml
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

Install the nvidia toolkit and restart docker using this link:
https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html
