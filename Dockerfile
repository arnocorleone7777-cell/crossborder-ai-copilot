FROM node:22-slim AS frontend
WORKDIR /build
COPY frontend/package*.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends fonts-dejavu-core && apt-get clean && find /var/lib/apt/lists -type f -delete
COPY requirements.lock ./
RUN pip install -r requirements.lock
COPY requirements.txt requirements-vector.txt ./
ARG INCLUDE_VECTOR=1
RUN if [ "$INCLUDE_VECTOR" = "1" ]; then pip install -r requirements-vector.txt; fi
COPY backend/ ./backend/
COPY --from=frontend /build/dist ./frontend/dist/
RUN useradd -m copilot && mkdir data generated && chown -R copilot:copilot /app
USER copilot
EXPOSE 8000
HEALTHCHECK --interval=20s --timeout=5s CMD python -c "import urllib.request,os; r=urllib.request.Request('http://127.0.0.1:8000/api/health'); t=os.getenv('API_TOKEN'); r.add_header('Authorization','Bearer '+t) if t else None; urllib.request.urlopen(r,timeout=3)"
CMD ["python","-m","uvicorn","backend.main:app","--host","0.0.0.0","--port","8000"]
