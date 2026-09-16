#!/bin/bash
set -e

PG_BIN=$(ls -d /usr/lib/postgresql/*/bin | head -1)
export PATH="$PG_BIN:$PATH"
PGDATA=${PGDATA:-/var/lib/postgresql/data}

if [ ! -s "$PGDATA/PG_VERSION" ]; then
    mkdir -p "$PGDATA"
    chown postgres:postgres "$PGDATA"
    su postgres -c "initdb -D $PGDATA --auth=trust"
    su postgres -c "pg_ctl -D $PGDATA -w start"
    su postgres -c "psql -c \"CREATE USER trolley WITH PASSWORD 'trolley';\""
    su postgres -c "psql -c \"CREATE DATABASE trolley OWNER trolley;\""
    su postgres -c "pg_ctl -D $PGDATA -w stop"
fi

exec supervisord -c /etc/supervisor/conf.d/supervisord.conf
