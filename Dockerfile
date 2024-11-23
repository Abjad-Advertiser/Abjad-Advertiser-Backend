FROM python:3.12.5 AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1
WORKDIR /app

# Install libmagic and file command
RUN python -m venv .venv
COPY requirements.txt ./
RUN .venv/bin/pip install -r requirements.txt

FROM python:3.12.5-slim
WORKDIR /app

# Copy virtual environment from builder stage
COPY --from=builder /app/.venv .venv/
COPY . .

# Ensure the virtual environment's bin directory is in the PATH
ENV PATH="/app/.venv/bin:$PATH"

# Use Uvicorn to run the FastAPI app
CMD ["python", "app/main.py"]