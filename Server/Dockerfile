# Server/Dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY . /app

RUN python -m venv venv && \
    . venv/bin/activate && \
    pip install --upgrade pip && \
    pip install -r requirements.txt

ENV VIRTUAL_ENV=/app/venv
ENV PATH="/app/venv/bin:$PATH"

CMD ["python", "mainServer.py"]
