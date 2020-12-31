#!/bin/sh

if [ "$DATABASE" = "postgres" ]
then
    echo "Waiting for postgres..."

    while ! nc -z db 5432; do
      sleep 0.1
    done

    echo "PostgreSQL started"
fi

./manage.py collectstatic --noinput
./manage.py migrate --noinput

exec "$@"
