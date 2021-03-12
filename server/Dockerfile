FROM python:3.8

RUN pip install -U --no-cache poetry==1.1.5

COPY manage.py pyproject.toml poetry.lock /app/

WORKDIR /app/

RUN poetry config virtualenvs.create false
RUN poetry install

COPY brator /app/brator

CMD ["gunicorn", "brator.asgi:application", "-k", "uvicorn.workers.UvicornWorker"]
