FROM python:3.11-slim

WORKDIR /app

# Install system deps for pdfplumber (poppler) and general build tools
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=8000
EXPOSE 8000

# Render (and most PaaS hosts) inject PORT at runtime
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT}
