#!/bin/sh

model="Qwen/Qwen2.5-Coder-7B-Instruct-GGUF/qwen2.5-coder-7b-instruct-q4_0.gguf"
model_identifier="qwen/qwen2.5-coder-7b-instruct"

# starting LM Studio server
lms server start

# loading Qwen2.5-Coder-7B-Instruct-GGUF model with quantization q4_0
lms load $model

echo "LM Studio server is ready!"