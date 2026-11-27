FROM ghcr.io/astral-sh/uv:0.9.6 AS uv
FROM python:3.11.15-slim
COPY --from=uv /uv /usr/local/bin/uv
WORKDIR /app
ENV UV_PROJECT_ENVIRONMENT=/opt/venv PATH="/opt/venv/bin:$PATH" UV_PYTHON_DOWNLOADS=never PHISHSHIELD_ROOT=/app PYTHONDONTWRITEBYTECODE=1
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --extra demo --no-install-project --no-cache
COPY src/phishshield ./src/phishshield
COPY configs/api.yaml ./configs/api.yaml
COPY .streamlit/config.toml .streamlit/config.toml
COPY MODEL_MANIFEST.json ./
ENV PYTHONPATH=/app/src HOME=/tmp
USER 65534:65534
CMD ["uvicorn","phishshield.api.app:app","--host","0.0.0.0","--port","8000"]

