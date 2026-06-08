import asyncio

import onnxruntime as rt
from sentence_transformers import SentenceTransformer

from app.models.parser import ParserSubgraph
from app.models.profiler import ProfileResult
from app.profiling_functions.base import BaseMLProfiler, Taxonomy

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
        cls.__INSTANCE = SentenceTransformer(instance_name)
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
            providers=["CPUExecutionProvider"],
        )
        return cls.__INSTANCE


class EmbeddingProfiler(BaseMLProfiler):
    def __init__(self, source_code: str, taxonomy: Taxonomy):
        super().__init__(source_code, taxonomy)

        self.embedding_model = EmbeddingModelSingleton.get_instance(
            "Qwen/Qwen3-Embedding-0.6B"
        )
        self.session = InferenceSessionSingleton.get_instance(
            "resources/SVC_mlpipelines_classifier_model.onnx",
        )

    async def profile_subgraph(self, subgraph: ParserSubgraph) -> ProfileResult:
        embedded_code = await asyncio.to_thread(self.embedding_model.encode, subgraph.source)
        input_name = self.session.get_inputs()[0].name
        label_name = self.session.get_outputs()[0].name
        predicted_class_id = self.session.run(
            [label_name],
            {input_name: embedded_code.reshape((1, embedded_code.shape[0]))},
        )[0][0]

        retrieved_step = LABELS_NAMES[predicted_class_id]
        return ProfileResult(step=retrieved_step, perplexity=-1)

    async def profile_multiple_subgraphs(self, subgraphs: list[ParserSubgraph]) -> list[ProfileResult]:
        embedded_code = await asyncio.to_thread(
            self.embedding_model.encode,
            [subgraph.source for subgraph in subgraphs],
        )
        input_name = self.session.get_inputs()[0].name
        label_name = self.session.get_outputs()[0].name
        predicted_class_id = self.session.run(
            [label_name], {input_name: embedded_code}
        )[0]
        return [ProfileResult(step=LABELS_NAMES[class_id], perplexity=-1) for class_id in predicted_class_id]
