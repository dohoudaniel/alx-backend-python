#!/usr/bin/env bash
set -e

# Optional: load environment variables from .env if you use python-dotenv
# (requires python-dotenv in requirements and a small script to load env vars)
# if [ -f .env ]; then
#   export $(grep -v '^#' .env | xargs)
# fi

echo "Starting entrypoint: running migrations and collecting static (if configured)..."

# Wait for DB if using Postgres (simple loop)
# If you use Postgres via docker-compose, uncomment and change host & port as needed
# echo "Waiting for database..."
# until nc -z -v -w30 "$DB_HOST" "$DB_PORT"; do
#   echo "Waiting for database at $DB_HOST:$DB_PORT..."
#   sleep 1
# done

# Run Django migrations and collectstatic
python manage.py migrate --noinput || {
  echo "Migrations failed"
  exit 1
}

# If you use collectstatic in production, uncomment the next line
# python manage.py collectstatic --noinput
# exec "$@"
