# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.14-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:0.11.32 /uv /uvx /bin/

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy from the cache instead of linking since it's a mounted volume
ENV UV_LINK_MODE=copy

RUN apt-get update \
    && apt-get install --no-install-recommends -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . /app

# install dependencies
COPY uv.lock pyproject.toml /app/
RUN uv sync --frozen --no-install-project --no-dev

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"

# Pull nlp model
RUN uv run /app/pkg/install.py

COPY docker.run.sh run.sh
RUN chmod +x run.sh

# Creates a non-root user with an explicit UID and adds permission to access the /app folder
# For more info, please refer to https://aka.ms/vscode-docker-python-configure-containers
RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser

ARG COMMIT=nightly
ENV RECIPES_PORT=8080
ENV RECIPES_HOST="0.0.0.0"
ENV RECIPES_COMMIT=$COMMIT

# Cap glibc per-thread arenas. Sync endpoints run across uvicorn's threadpool;
# without this, each thread gets its own arena and freed memory fragments across
# them, ballooning RSS under load (measured: 8-thread retained 190 -> 119 MiB).
ENV MALLOC_ARENA_MAX=2

EXPOSE 8080

# During debugging, this entry point will be overridden. For more information, please refer to https://aka.ms/vscode-docker-python-debug
ENTRYPOINT [ "./run.sh" ]