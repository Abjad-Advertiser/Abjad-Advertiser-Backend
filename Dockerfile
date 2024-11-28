FROM python:3.12.5 AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 
WORKDIR /app

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

CMD ["uvicorn", "app.app:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--log-level", "debug"]