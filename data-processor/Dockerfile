FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY pyproject.toml README.md ./
COPY app ./app
COPY data-processor/processor.py ./data-processor/processor.py
RUN pip install --no-cache-dir -e .

CMD ["python", "data-processor/processor.py"]
