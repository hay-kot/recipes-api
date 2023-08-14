###############################################
# CRFPP Image
###############################################
FROM hkotel/crfpp as crfpp

RUN echo "crfpp-container"

# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.11-slim

EXPOSE 8000

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Install deps for lxml
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    # zlib
    zlib1g-dev \
    libxml2-dev \
    libxslt-dev

# Install pip requirements
COPY requirements.txt .
RUN python -m pip install -r requirements.txt


WORKDIR /app
COPY . /app

ENV LD_LIBRARY_PATH=/usr/local/lib
COPY --from=crfpp /usr/local/lib/ /usr/local/lib
COPY --from=crfpp /usr/local/bin/crf_learn /usr/local/bin/crf_learn
COPY --from=crfpp /usr/local/bin/crf_test /usr/local/bin/crf_test

# Grab CRF++ Model Release
RUN python /app/install.py

# Creates a non-root user with an explicit UID and adds permission to access the /app folder
# For more info, please refer to https://aka.ms/vscode-docker-python-configure-containers
RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser

# During debugging, this entry point will be overridden. For more information, please refer to https://aka.ms/vscode-docker-python-debug
CMD ["uvicorn", "--host", "0.0.0.0", "--port", "8000", "main:app"]
