#!/bin/sh
# How the container starts (dev_environment_and_deployment.md §3, ADR-086).
# MIGRATE_ON_START=1 applies migrations and runs the (idempotent) seed first, for hosts with
# no shell to run them from, such as Render's free plan. Hosts with a shell leave it at 0
# and run `manage.py migrate --database=direct` themselves before starting the new version.
set -eu

if [ "${MIGRATE_ON_START:-0}" = "1" ]; then
    python manage.py migrate --database=direct --noinput
    python manage.py seed
fi

# PORT is set by hosts that choose it (Render); 8000 everywhere else
exec gunicorn config.wsgi -k gthread \
    --workers "${WEB_CONCURRENCY:-2}" --threads 4 --timeout 30 \
    --bind "0.0.0.0:${PORT:-8000}" --access-logfile -
