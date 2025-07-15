#!/bin/sh

# expects the MODEL_ID environment variable to be set.

# pulling model
docker exec -ti profil-platform-poc-profil_ollama-1 ollama pull $MODEL_ID || exit 1

echo "$MODEL_ID is ready!"
