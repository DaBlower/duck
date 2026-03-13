# Use Python 3.13.5 
FROM python:3.13.5-slim

# set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/home/appuser/.local/bin:${PATH}"

RUN useradd --create-home appuser
RUN mkdir /app

RUN chown appuser:appuser /app

# Working directory
WORKDIR /app

RUN mkdir -p /app/db /app/logs && \
    chown -R appuser:appuser /app/db /app/logs/

COPY --chown=appuser:appuser requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

COPY --chown=appuser:appuser src/ ./src/

USER appuser

VOLUME [ "/app/db", "/app/logs" ]

CMD ["python", "src/main.py"]