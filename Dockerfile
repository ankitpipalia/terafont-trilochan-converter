# Lightweight test container.
# Only runs the pure-Python conversion tests — no OCR / no PyWebView.
#
# Build:  docker compose build
# Run:    docker compose run --rm test

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Copy only what's needed for the test suite
COPY pyproject.toml requirements-slim.txt requirements-dev.txt ./
COPY app/converter.py app/converter.py
COPY app/__init__.py app/__init__.py
COPY tests/ tests/

# Touch optional ocr package marker so imports don't fail if tests import siblings
RUN mkdir -p app/ocr && touch app/ocr/__init__.py

RUN pip install --no-cache-dir pytest

CMD ["python", "-m", "pytest", "tests/test_converter.py", "-v", "--tb=short"]
