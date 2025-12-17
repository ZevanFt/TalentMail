#!/bin/sh
# wait-for-postgres.sh

set -e

host="$1"
shift

# Skip the '--' separator if present
if [ "$1" = "--" ]; then
  shift
fi

cmd="$@"

until PGPASSWORD=$POSTGRES_PASSWORD psql -h "$host" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c '\q'; do
  >&2 echo "Postgres is unavailable - sleeping"
  sleep 1
done

>&2 echo "Postgres is up - executing command"
exec $cmd
