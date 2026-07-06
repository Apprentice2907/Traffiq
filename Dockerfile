FROM python:3.11-slim

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/
COPY data.csv .

WORKDIR /app/backend

ENV DATA_PATH=/app/data.csv
ENV MODELS_DIR=/app/backend/models
ENV HF_SPACE=true

RUN mkdir -p models

CMD ["uvicorn", "app_hf:app", "--host", "0.0.0.0", "--port", "7860"]
