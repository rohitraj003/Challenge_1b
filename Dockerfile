FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1

WORKDIR /app


COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt


COPY round1b /app/round1b

ENTRYPOINT ["python", "round1b/main.py", "/app/input", "/app/input_json", "/app/output"]
