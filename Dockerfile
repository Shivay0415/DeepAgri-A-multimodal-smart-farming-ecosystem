FROM node:20-alpine AS frontend-build

WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN mkdir -p /app/backend && npm run build

FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

WORKDIR /app/backend

COPY backend/requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY backend/ /app/backend/
COPY --from=frontend-build /app/backend/frontend_dist /app/backend/frontend_dist

RUN python manage.py bootstrap_demo_models && python manage.py collectstatic --noinput

EXPOSE 10000

CMD ["/bin/sh", "-c", "python manage.py migrate && gunicorn agri_platform.wsgi:application --bind 0.0.0.0:${PORT:-10000}"]
