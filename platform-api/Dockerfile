FROM python:3.12-slim

WORKDIR /workspace

RUN apt-get update \
    && apt-get install -y --no-install-recommends ansible ca-certificates curl openssh-client \
    && rm -rf /var/lib/apt/lists/*

COPY platform-api/requirements.txt /workspace/platform-api/requirements.txt
RUN pip install --no-cache-dir -r /workspace/platform-api/requirements.txt

# Copy the whole repository because the API executes existing playbooks, roles, inventories and scripts.
COPY . /workspace

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/workspace/platform-api
ENV PROJECT_ROOT=/workspace

EXPOSE 8080

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
