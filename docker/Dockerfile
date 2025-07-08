FROM ghcr.io/astral-sh/uv:python3.12-bookworm
ADD . /app
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1
RUN uv sync --locked
ENV PATH="/app/.venv/bin:$PATH"
ENTRYPOINT []
CMD ["fastapi", "dev", "--host", "0.0.0.0", "src/main.py", "--proxy_headers"]
