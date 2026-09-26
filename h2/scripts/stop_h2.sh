#!/usr/bin/env bash
# Mata el server H2 si existe. Equivalente Linux de stop_h2.bat.
# Al parar el server, la BD in-memory mem:csep se limpia sola.
set -euo pipefail

echo "Deteniendo H2 Server si existe..."
pkill -f 'org.h2.tools.Server' 2>/dev/null || true
sleep 2

echo "Stop H2 listo"