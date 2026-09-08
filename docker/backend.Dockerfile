FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 DATA_DIR=/data UPLOADS_DIR=/uploads BACKUPS_DIR=/backups
WORKDIR /app
COPY backend/requirements*.txt ./
RUN if [ -f requirements-ci.txt ]; then pip install --no-cache-dir -r requirements.txt -c requirements-ci.txt; else pip install --no-cache-dir -r requirements.txt; fi
RUN useradd --uid 10001 --create-home filmhub && mkdir /data /uploads /backups && chown -R filmhub:filmhub /data /uploads /backups
COPY --chown=filmhub:filmhub backend/app ./app
USER filmhub
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health',timeout=4)"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
