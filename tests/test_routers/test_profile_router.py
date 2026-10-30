import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.notebooks import NotebookInformation
from app.models.parser import ParserFunction
from app.models.profiler import ProfilerFunction
from app.models.taxonomy import TaxonomyFunction
from app.routers.profile_router import _profile_notebook

client = TestClient(app)

example_of_notebook_info = NotebookInformation(name='test_file', parser_model=[], source_code="def f(x):" \
"   return x+2", parser_function=ParserFunction.VESPUCCI)

@pytest.mark.asyncio
async def test_profile_notebook():

    result = await _profile_notebook(example_of_notebook_info, taxonomy_name=TaxonomyFunction.DSPIPELINES, profiler_name=ProfilerFunction.DSPIPELINES)

    assert result['name'] == 'test_file'
    assert not result['source']
    assert not result['outputs']

def test_profile():
    response = client.post("/v2/profile", params={'taxonomy': TaxonomyFunction.DSPIPELINES.value,'profiler': ProfilerFunction.DSPIPELINES.value}, json={'data': [example_of_notebook_info.model_dump()]})
    print(response.json())
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]['name'] == 'test_file'
    assert not response.json()[0]['outputs']
