FROM python:3.14-slim-trixie

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    OMP_THREAD_LIMIT=1 \
    OPENBLAS_NUM_THREADS=1 \
    PORT=8000

RUN apt-get update \
    && apt-get install -y --no-install-recommends tesseract-ocr tesseract-ocr-eng libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt requirements-hosted.txt ./
RUN python -m pip install --no-cache-dir -r requirements-hosted.txt

COPY server.py app.py gunicorn.conf.py index.html ./
RUN useradd --system --uid 10001 --create-home digitizer
USER digitizer

EXPOSE 8000
CMD ["gunicorn", "--config", "gunicorn.conf.py", "app:app"]
