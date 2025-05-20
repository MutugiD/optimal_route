# ─────────────────────────────
# 1. Base image
# ─────────────────────────────
FROM python:3.10-slim

# ─────────────────────────────
# 2. Environment
# ─────────────────────────────
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=optimal_api.settings

# ─────────────────────────────
# 3. Workdir
# ─────────────────────────────
WORKDIR /app

# ─────────────────────────────
# 4. System-level deps
# ─────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# ─────────────────────────────
# 5. Copy *only* packaging metadata first
#    (maximises Docker layer cache when
#     code changes but deps don’t)
# ─────────────────────────────
COPY setup.py ./

# ─────────────────────────────
# 6. Install project + runtime deps
#    Everything declared under
#    install_requires in setup.py
#    (or pyproject.toml) will be pulled in.
# ─────────────────────────────
RUN pip install --no-cache-dir .

# ─────────────────────────────
# 7. Copy the rest of the source
# ─────────────────────────────
COPY . .

# ─────────────────────────────
# 8. Collect static files
# ─────────────────────────────
RUN python manage.py collectstatic --noinput

# ─────────────────────────────
# 9. Runtime
# ─────────────────────────────
EXPOSE 8000
CMD ["gunicorn", "optimal_api.wsgi:application", "--bind", "0.0.0.0:8000"]
