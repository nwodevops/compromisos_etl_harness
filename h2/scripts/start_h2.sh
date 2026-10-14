#!/usr/bin/env bash
# Levanta el server H2 (TCP 9092 + WEB 8082). Equivalente Linux de start_h2.bat.
set -euo pipefail

cd "$(dirname "$(readlink -f "$0")")/.."

H2_JAR="lib/h2-2.4.240.jar"
[ -f "$H2_JAR" ] || H2_JAR="h2-2.4.240.jar"
H2_PORT="${H2_PORT:-9092}"
H2_WEB_PORT="${H2_WEB_PORT:-8082}"
H2_LOG="h2_server.log"

if [ ! -f "$H2_JAR" ]; then
  echo "FAIL: no se encontro el jar de H2 ($H2_JAR)" >&2
  exit 1
fi

port_up() {
  if command -v ss >/dev/null 2>&1; then
    ss -ltn 2>/dev/null | grep -qE ":${H2_PORT}[[:space:]]"
  else
    netstat -ltn 2>/dev/null | grep -qE ":${H2_PORT}[[:space:]]"
  fi
}

if port_up; then
  echo "H2 ya esta arriba en puerto ${H2_PORT}"
  exit 0
fi

echo "Levantando H2 TCP+WEB..."
# La accion SHELL de Hop espera a que se cierren los descriptores heredados:
# sin redirigir stdout/stderr y sin nohup, el workflow se cuelga para siempre.
nohup java -cp "$H2_JAR" org.h2.tools.Server \
  -tcp -web -webPort "$H2_WEB_PORT" -tcpPort "$H2_PORT" -ifNotExists \
  >"$H2_LOG" 2>&1 &
disown

for _ in $(seq 1 30); do
  if port_up; then
    echo "H2 OK puerto ${H2_PORT}"
    exit 0
  fi
  sleep 1
done

echo "FAIL: H2 no abrio puerto ${H2_PORT}. Revisa ${H2_LOG}" >&2
exit 1