###############################################
# CRFPP Image
###############################################
FROM hkotel/crfpp as crfpp

ARG COMMIT

RUN echo "crfpp-container"

# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.11-slim


WORKDIR /app
COPY . /app

ENV LD_LIBRARY_PATH=/usr/local/lib
COPY --from=crfpp /usr/local/lib/ /usr/local/lib
COPY --from=crfpp /usr/local/bin/crf_learn /usr/local/bin/crf_learn
COPY --from=crfpp /usr/local/bin/crf_test /usr/local/bin/crf_test

ENV PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VERSION=1.7.0


# System deps:
RUN pip install "poetry==$POETRY_VERSION"

# install dependencies
COPY poetry.lock pyproject.toml /app/

RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root --all-extras

# Grab CRF++ Model Release
RUN python /app/install.py

COPY docker.run.sh run.sh
RUN chmod +x run.sh

# Creates a non-root user with an explicit UID and adds permission to access the /app folder
# For more info, please refer to https://aka.ms/vscode-docker-python-configure-containers
RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser

ENV PORT 8000
ENV HOST "0.0.0.0"
ENV COMMIT $COMMIT

EXPOSE 8000

# During debugging, this entry point will be overridden. For more information, please refer to https://aka.ms/vscode-docker-python-debug
ENTRYPOINT [ "./run.sh" ]
