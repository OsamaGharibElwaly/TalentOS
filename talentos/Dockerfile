# syntax=docker/dockerfile:1

# Builder: install the declared project into an isolated virtualenv.
FROM python:3.11-slim AS builder
WORKDIR /build
COPY pyproject.toml ./
COPY app ./app
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir --disable-pip-version-check .

# Runtime: slim image carrying only the virtualenv and application source.
FROM python:3.11-slim AS runtime
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TALENTOS_DATA_DIR=/data
WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
COPY app ./app
VOLUME ["/data"]
EXPOSE 8000
CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
