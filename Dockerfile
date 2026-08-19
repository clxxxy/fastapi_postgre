FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml ./
COPY app ./app
COPY migrations ./migrations
COPY tests ./tests
COPY alembic.ini ./

RUN python -m pip install --no-cache-dir -e ".[test]"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]