FROM python:3.12-slim
WORKDIR /app
COPY backend/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
COPY backend /app/backend
WORKDIR /app/backend
CMD ["python", "-m", "app.workers.celery_worker"]
