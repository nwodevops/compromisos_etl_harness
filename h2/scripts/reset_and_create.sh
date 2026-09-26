#!/usr/bin/env bash
# Reset clean de H2 in-memory + DDL del proyecto. Equivalente Linux de
# reset_and_create.bat.
#
# En Linux el server se para y se levanta aqui mismo (nohup + redireccion, sin
# la consola de Hop), por lo que no hace falta la tarea programada
# start_h2_svc.bat. En Windows reset_and_create.bat SOLO verifica el puerto:
# el server corre como tarea independiente (start_h2_svc.bat).
#
# H2 es in-memory (mem:csep): al parar el server se limpia sola. El reset no
# ejecuta sql/02_stg.sql (eso lo hace python/create_stg.py).
set -euo pipefail

cd "$(dirname "$(readlink -f "$0")")/.."

H2_JAR="lib/h2-2.4.240.jar"
[ -f "$H2_JAR" ] || H2_JAR="h2-2.4.240.jar"
DB_H2_URL="jdbc:h2:tcp://localhost:9092/mem:csep;DB_CLOSE_DELAY=-1;MODE=Oracle;DATABASE_TO_UPPER=TRUE;DEFAULT_NULL_ORDERING=HIGH;AUTO_RECONNECT=TRUE"

run_script() {
  java -cp "$H2_JAR" org.h2.tools.RunScript \
    -url "$DB_H2_URL" -user sa -password csep -script "$1"
}

echo "=== Stop H2 (limpia mem) ==="
scripts/stop_h2.sh

echo "=== Start H2 TCP (mem:csep) ==="
if ! scripts/start_h2.sh; then
  echo "FAIL start" >&2
  exit 1
fi

echo "=== Aplicar DDL (sql/00_reset.sql) ==="
if ! run_script "sql/00_reset.sql"; then
  echo "FAIL reset" >&2
  exit 1
fi

echo "=== Aplicar DDL (sql/01_schema.sql) ==="
if ! run_script "sql/01_schema.sql"; then
  echo "FAIL schema" >&2
  exit 1
fi

echo "=== Reset+Create OK ==="
echo "Pipelines / logica usan: ${DB_H2_URL}"
exit 0