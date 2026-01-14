FROM python:3.10-slim

WORKDIR /app

# Copy requirements first for potential caching (context is ./backend)
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy source code into a 'backend' subdirectory to preserve package structure
# This allows 'from . import' to work correctly when running as a module
COPY . backend/

# Prevent Python from writing pyc files to disc (useful when using volumes)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Run the app as a module: backend.main:app
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
