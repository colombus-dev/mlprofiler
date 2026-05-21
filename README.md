# ML Profiler setup guide

## Requirements

* Docker (tested on version 28.5.1, build e180ab8)
* Docker Compose (tested on version v2.40.0)
* Docker Model Runner [through the Docker Engine on Linux](https://docs.docker.com/ai/model-runner/get-started/#docker-engine) (tested on version v1.1.37), or [through Docker Desktop on Mac](https://docs.docker.com/ai/model-runner/get-started/#docker-desktop)

## Configuring DMR

The model and inference engine differ by platform.

### 1. Linux:

[Setup vLLM](https://docs.docker.com/ai/model-runner/inference-engines/#setting-up-vllm)
```bash
docker model install-runner --backend vllm --gpu cuda
```

Configuring the model
```bash
docker model configure --hf_overrides '{
  "max_model_len": 8192,
  "max_num_seqs": 10,
  "gpu_memory_utilization": 0.8,
  "enforce_eager": true
}' hf.co/Qwen/Qwen2.5-Coder-7B-Instruct-AWQ
```

Inspecting the configuration
```bash
docker model configure show
```

### 2. Mac

No extra installation needed. DMR uses llama.cpp by default, which runs natively on Apple Silicon via Metal.
Model configuration TBD.

## Starting the app

Go inside the docker folder by running : ```cd docker```

Prepare the env file
```bash
cp .env.sample .env
```
> [!IMPORTANT]
> Make sure your edit '.env' to update the variable so that they fit your needs.

Then follow one of the below procedures :

* Linux (vLLM image, requires the variable FORCE_VLLM=1)
  ```bash
  docker compose -f docker-compose.yml -f docker-compose.linux.dmr.yml -f docker-compose.linux.vllm.yml --env-file .env up --build
  ```
* Linux (DMR)
  ```bash
  docker compose -f docker-compose.yml -f docker-compose.linux.dmr.yml --env-file .env up --build
  ```
* Mac
  ```bash
  docker compose -f docker-compose.yml -f docker-compose.mac.yml --env-file .env up --build
  ```

It's also possible to deploy the monitoring as follows:

* Langfuse - [doc](https://langfuse.com/docs)
  ```bash
  docker compose -f docker-compose-monitor-langfuse.yml up
  ```
* Grafana - [doc](https://github.com/vllm-project/vllm/tree/main/examples/online_serving/prometheus_grafana#prometheus-and-grafana)
  ```bash
  docker compose -f docker-compose-monitor-grafana.yml up
  ```

## Development

We use pre-commit to ensure code quality. Install pre-commit hooks locally:
```bash
uv run --with pre-commit pre-commit install
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
