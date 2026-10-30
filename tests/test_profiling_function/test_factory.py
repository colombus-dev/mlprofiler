import pytest

from app.models.profiler import ProfilerFunction
from app.models.taxonomy import TAXONOMY_BY_NAME, TaxonomyFunction
from app.profiling_functions.dspipelines import DSPipelinesProfiler
from app.profiling_functions.embedding import EmbeddingProfiler
from app.profiling_functions.factory import get_profiler
from app.profiling_functions.headergen import HeaderGenProfiler
from app.profiling_functions.llm import LLMProfiler


@pytest.mark.parametrize("profiler_name, resulting_class", [
    (ProfilerFunction.EMBEDDING, EmbeddingProfiler),
    (ProfilerFunction.HEADERGEN, HeaderGenProfiler),
    (ProfilerFunction.LLM, LLMProfiler),
    (ProfilerFunction.DSPIPELINES, DSPipelinesProfiler),
])
def test_get_profiler_success(profiler_name, resulting_class):

    result = get_profiler('', TAXONOMY_BY_NAME[TaxonomyFunction.DSPIPELINES], profiler_name)

    assert type(result) == resulting_class


def test_get_profiler_fails():

    with pytest.raises(ValueError):
        get_profiler('', TAXONOMY_BY_NAME[TaxonomyFunction.DSPIPELINES], 'random_profiler')
