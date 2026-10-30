import pytest

from app.models.parser import ParserSubgraph, ParserSubgraphCursor, ParserSubgraphLine
from app.models.taxonomy import TAXONOMY_BY_NAME, TaxonomyFunction
from app.profiling_functions.dspipelines import DSPipelinesProfiler


def test_initialisation():

    profiler_test = DSPipelinesProfiler('def f(x):\n    return x**2', TAXONOMY_BY_NAME[TaxonomyFunction.DSPIPELINES])

    assert profiler_test._source_code == 'def f(x):\n    return x**2'
    assert profiler_test._source_code_split == ['def f(x):', '    return x**2']
    assert profiler_test._taxonomy == TAXONOMY_BY_NAME[TaxonomyFunction.DSPIPELINES]
    assert profiler_test._session_id.startswith('session-')

def test_compute_source_code_context():

    profiler_test = DSPipelinesProfiler('def f(x):\n    return x**2\nmy_numer=5\nprint(f(my_number))\ncalcul=5+78\nprint(calcul<f(my_number))', TAXONOMY_BY_NAME[TaxonomyFunction.DSPIPELINES])

    result = profiler_test.compute_source_code_context(2, 2)

    assert result == 'def f(x):\n    return x**2\nmy_numer=5\nprint(f(my_number))'

@pytest.mark.asyncio
@pytest.mark.parametrize("subgraph_function, expected_result", [
    ("subplot", "Interpretation"),
    ("permutation", "Data Preparation"),
    ("l2_loss", "Modeling"),
    ("show_prediction", "Prediction"),
    ("ReduceLROnPlateau", "Modeling"),
    ("evaluate", "Evaluation"),
    ("from_records", "Data Acquisition"),
    ("some_random_function", "Other")
])
async def test_profile_subgraph(subgraph_function, expected_result):

    profiler_test = DSPipelinesProfiler('', TAXONOMY_BY_NAME[TaxonomyFunction.DSPIPELINES])

    profile_result = await profiler_test.profile_subgraph(ParserSubgraph(id='', library='', function=subgraph_function, source='', step_name='', line=ParserSubgraphLine(start=1, end=2), cursor=ParserSubgraphCursor(start=1, end=2)))

    assert profile_result.step == expected_result
    assert profile_result.perplexity ==1
