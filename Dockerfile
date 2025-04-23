FROM python:3.12-slim

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./templates/ /code/templates/

COPY ./resources/ /code/resources/

COPY src/main.py src/utils.py src/__init__.py /code/app/

CMD ["fastapi", "run", "app/main.py", "--host", "0.0.0.0", "--port", "8081"]
