FROM python:3.12-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends ansible ca-certificates curl openssh-client \
    && rm -rf /var/lib/apt/lists/*

COPY platform-api/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY platform-api/app /app/app

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

EXPOSE 8080

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
