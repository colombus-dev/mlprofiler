FROM nlacroix101/mlprofile:base-0.1 AS llm-api-builder

LABEL version="0.1"
LABEL description="This is the image used to build the LLM API."

COPY pyproject.toml poetry.lock ./

# Required to install the poetry-export plugin
# TODO: limit install to plugin only (currently installing all dependencies from pyproject.toml)
RUN poetry install --no-cache

RUN poetry export --only core,llm --without-hashes --format=requirements.txt > requirements.txt

RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

FROM python:3.12-alpine3.21 AS llm-api-runner

LABEL version="0.1"
LABEL description="This is the image used to run the LLM API."

WORKDIR /code

COPY --from=llm-api-builder /code/requirements.txt ./

COPY --from=llm-api-builder /wheels /wheels

RUN pip install --no-cache-dir --no-index --no-deps --find-links=/wheels -r requirements.txt \
    && rm -rf /wheels/
    
RUN adduser -D standarduser

RUN chown -R standarduser:standarduser /code

USER standarduser

COPY ./common/ /code/common/

COPY ./llm/templates/ /code/templates/

COPY ./llm/resources/ /code/resources/

COPY ./llm/app/ /code/app/

CMD ["fastapi", "run", "app/main.py", "--host", "0.0.0.0", "--port", "8081"]
