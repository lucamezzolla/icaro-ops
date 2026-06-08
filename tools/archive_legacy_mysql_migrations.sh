#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

mkdir -p db/mysql/archive_legacy_migrations
find db/mysql -maxdepth 1 -type f -name '*.sql' ! -name '000_bootstrap_icaro_ops.sql' -print -exec mv {} db/mysql/archive_legacy_migrations/ \;

echo "Legacy SQL files moved to db/mysql/archive_legacy_migrations/."
echo "Review and delete the archive after testing 000_bootstrap_icaro_ops.sql."
