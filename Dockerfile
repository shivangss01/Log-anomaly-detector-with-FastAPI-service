FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create the synthetic access.log inside the image
RUN python generate_logs.py

# Hosting platforms like Render set $PORT; default to 8000 locally
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
