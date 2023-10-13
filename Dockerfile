###############################################
# CRFPP Image
###############################################
FROM hkotel/crfpp as crfpp

ARG COMMIT

RUN echo "crfpp-container"

# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.11-slim

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Install pip requirements
COPY requirements.txt .
RUN python -m pip install -r requirements.txt --only-binary=lxml


WORKDIR /app
COPY . /app

ENV LD_LIBRARY_PATH=/usr/local/lib
COPY --from=crfpp /usr/local/lib/ /usr/local/lib
COPY --from=crfpp /usr/local/bin/crf_learn /usr/local/bin/crf_learn
COPY --from=crfpp /usr/local/bin/crf_test /usr/local/bin/crf_test

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
