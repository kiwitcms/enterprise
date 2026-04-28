#!/bin/bash

# Copyright (c) 2026 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

# When starting a new DB server:
#
# 0. provide your SSL certificate as database.crt and database.key files
# 1. bind-mount this directory inside the container as /docker-entrypoint-initdb.d/
# 2. add ?sslmode=require to your DATABASE_URL ENV variable or
#    specify DATABASES['default']['OPTIONS']['sslmode'] = 'require'
#
# For an already running DB server:
# 0. copy certificates as $PGDATA/server.key & $PGDATA/server.crt
#    chown postgres:postgres && chmod 0600
# 1. alter system settings & pg_hbs.conf if necessary
# 2. restart DB server

set -eu

SSL_CERT_FILE="$(dirname $0)/database.crt"
SSL_KEY_FILE="$(dirname $0)/database.key"

[ ! -f "$SSL_CERT_FILE" ] && exit 1
[ ! -f "$SSL_KEY_FILE" ] && exit 1

[ ! -r "$SSL_CERT_FILE" ] && exit 2
[ ! -r "$SSL_KEY_FILE" ] && exit 2

# IMPORTANT: to refresh these certificates copy them
# directly under $PGDATA once the server has been initialized
# WARNING: chown postgres:postgres
# WARNING: chmod 0600
echo "    **** Configure SSL certificate and key"
cp "$SSL_CERT_FILE" "$PGDATA/server.crt"
chown postgres:postgres "$PGDATA/server.crt"
chmod 0600  "$PGDATA/server.crt"
ls -l "$PGDATA/server.crt"

cp "$SSL_KEY_FILE" "$PGDATA/server.key"
chown postgres:postgres "$PGDATA/server.key"
chmod 0600  "$PGDATA/server.key"
ls -l "$PGDATA/server.key"

echo "    **** Turn SSL mode ON"
psql --set ON_ERROR_STOP=1 \
    --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    ALTER SYSTEM SET ssl TO 'ON';
EOSQL

echo "    **** Require SSL connections from clients"
sed -i "s/host all all all scram-sha-256/hostssl all all all scram-sha-256/" "$PGDATA/pg_hba.conf"
echo "# Explicitly reject non-SSL connections" >> "$PGDATA/pg_hba.conf"
echo "hostnossl all all all reject" >> "$PGDATA/pg_hba.conf"
cat "$PGDATA/pg_hba.conf"
