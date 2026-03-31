# Hugging Face Spaces (Docker) or any container host
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt pyproject.toml README.md ./
COPY blamebug ./blamebug
COPY app.py ./

RUN pip install --no-cache-dir -U pip && pip install --no-cache-dir .

ENV GRADIO_SERVER_NAME=0.0.0.0
EXPOSE 7860

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]
