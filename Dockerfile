FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY pyproject.toml uv.lock ./

RUN pip install --no-cache-dir uv \
    && uv sync --frozen --no-dev

COPY app ./app
COPY prompts ./prompts

EXPOSE 8000

CMD ["uv", "run", "--no-dev", "uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
