FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir fastapi uvicorn redis pydantic pydantic-settings
COPY websocket-service /app/websocket-service
WORKDIR /app/websocket-service
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8010", "--reload"]
