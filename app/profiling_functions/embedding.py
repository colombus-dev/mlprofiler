import os

import numpy as np
import onnxruntime as rt
from sentence_transformers import SentenceTransformer

from app.custom_types import ParserSubgraph
from app.profiling_functions._base import BaseMLProfiler, Taxonomy


INFERENCE_API_URL = os.getenv("INFERENCE_API_URL", "mlprofiler_vllm:11434")

LABELS_NAMES = [
    "Data Preparation",
    "Data Collection",
    "Model Evaluation",
    "Data Modeling",
    "Model Deployment",
    "Save Results",
]


class EmbeddingModelSingleton:
    __INSTANCE: SentenceTransformer | None = None
    __INSTANCE_NAME: str = ""

    @classmethod
    def get_instance(cls, instance_name: str) -> SentenceTransformer:
        if cls.__INSTANCE and cls.__INSTANCE_NAME == instance_name:
            return cls.__INSTANCE
        cls.__INSTANCE_NAME = instance_name
        cls.__INSTANCE = SentenceTransformer(instance_name, device="cuda")
        return cls.__INSTANCE


class InferenceSessionSingleton:
    __INSTANCE: rt.InferenceSession | None = None
    __INSTANCE_NAME: str = ""

    @classmethod
    def get_instance(cls, instance_name: str) -> SentenceTransformer:
        if cls.__INSTANCE and cls.__INSTANCE_NAME == instance_name:
            return cls.__INSTANCE
        cls.__INSTANCE_NAME = instance_name
        cls.__INSTANCE = rt.InferenceSession(
            instance_name,
            providers=["CUDAExecutionProvider", "CPUExecutionProvider"],
        )
        return cls.__INSTANCE


class EmbeddingProfiler(BaseMLProfiler):
    def __init__(self, python_content: str, taxonomy: Taxonomy):
        super().__init__(python_content, taxonomy)

        self.embedding_model = EmbeddingModelSingleton.get_instance(
            "Qwen/Qwen3-Embedding-0.6B"
        )
        self.session = InferenceSessionSingleton.get_instance(
            "resources/SVC_mlpipelines_classifier_model.onnx",
        )

    @BaseMLProfiler.python_content.setter
    def python_content(self, new_content):
        self._python_content = new_content

    def profile_subgraph(
        self,
        subgraph: ParserSubgraph,
        default_step: str,
        expected: str | list[str] | None = None,
    ) -> tuple[str, float | None, list[list[tuple[str, float]]]]:
        embedded_code = self.embedding_model.encode(subgraph.source)
        input_name = self.session.get_inputs()[0].name
        label_name = self.session.get_outputs()[0].name
        # predicted_class_id = self.session.run([label_name], {input_name: embedded_code})[0]
        predicted_class_id = self.session.run(
            [label_name],
            {input_name: embedded_code.reshape((1, embedded_code.shape[0]))},
        )[0][0]

        retrieved_step = LABELS_NAMES[
            predicted_class_id
        ]  # self.taxonomy.get_steps_names()[predicted_class_id]
        return (
            retrieved_step,
            -1,
            [],
        )

    def profile_multiple_subgraphes(
        self,
        subgraphes: list[ParserSubgraph],
        default_step: str,
        expected: list[str | list[str]] | None = None,
    ) -> list[tuple[str, float | None, list[list[tuple[str, float]]]]]:
        embedded_code = self.embedding_model.encode(
            [subgraph.source for subgraph in subgraphes]
        )
        input_name = self.session.get_inputs()[0].name
        label_name = self.session.get_outputs()[0].name
        predicted_class_id = self.session.run(
            [label_name], {input_name: embedded_code}
        )[0]
        return [(LABELS_NAMES[class_id], -1, []) for class_id in predicted_class_id]
