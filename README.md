# ML Profiler

Profiles ML pipelines by analyzing source code and classifying pipeline steps.

## Requirements

- Docker ≥ 28.5.1
- Docker Compose ≥ 2.40.0
- _(Advanced)_ [Docker Model Runner](https://docs.docker.com/ai/model-runner/get-started/) ≥ 1.1.37 required for the LLM profiler function

## Quick start

```bash
cd docker
cp .env.sample .env # edit .env if needed, the defaults work for basic setup
docker compose --env-file .env up --build
```

## Advanced setup (LLM profiler)

The LLM profiler function requires Docker Model Runner (DMR). Setup differs by platform.

### Mac DMR

No extra installation needed. DMR uses llama.cpp natively via Metal (Apple Silicon).

```bash
docker compose -f docker-compose.yml -f docker-compose.mac.yml --env-file .env up --build
```

### Linux DMR

[Set up the vLLM inference backend](https://docs.docker.com/ai/model-runner/inference-engines/#setting-up-vllm):

```bash
docker model install-runner --backend vllm --gpu cuda
```

[Configure the model](https://docs.docker.com/ai/model-runner/inference-engines/#vllm-configuration):

```bash
docker model configure --hf_overrides '{
  "max_model_len": 8192,
  "max_num_seqs": 10,
  "gpu_memory_utilization": 0.8,
  "enforce_eager": true
}' hf.co/Qwen/Qwen2.5-Coder-7B-Instruct-AWQ
```

```bash
docker compose -f docker-compose.yml -f docker-compose.linux.dmr.yml --env-file .env up --build
```

### Linux vLLM (standalone)

Set `VLLM_FORCE=1` in `.env`, then:

```bash
docker compose -f docker-compose.yml -f docker-compose.linux.dmr.yml -f docker-compose.linux.vllm.yml --env-file .env up --build
```

## Monitoring (optional)

| Stack | Command |
|---|---|
| Langfuse ([docs](https://langfuse.com/docs)) | `docker compose -f docker-compose-monitor-langfuse.yml up` |
| Grafana/Prometheus ([docs](https://github.com/vllm-project/vllm/tree/main/examples/online_serving/prometheus_grafana)) | `docker compose -f docker-compose-monitor-grafana.yml up` |

## Development

Install pre-commit hooks:

```bash
uv run --with pre-commit pre-commit install
```

## Troubleshooting

**`permission denied` connecting to Docker socket**
```bash
sudo usermod -a -G docker $USER && newgrp docker
```
Then reboot.

---

**`uv sync` fails during build**

Regenerate the lockfile:
```bash
uv lock
```

---

**`colombus-dev_network` not found**
```bash
docker network create colombus-dev_network
```

---

**`could not select device driver "nvidia"`**

Install the [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html#with-apt-ubuntu-debian) and [configure Docker to use the NVIDIA runtime](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html#configuring-docker).
