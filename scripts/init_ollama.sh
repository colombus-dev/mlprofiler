#!/bin/sh

# config
model_identifier="qwen2.5-coder:7b"

# pulling model
docker exec -ti profil-platform-poc-profil_ollama-1 ollama pull $model_identifier

echo "$model_identifier is ready!"
