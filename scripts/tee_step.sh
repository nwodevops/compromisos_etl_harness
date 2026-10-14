#!/bin/sh
# Guarda la salida de un paso y la muestra.
# Uso: ./scripts/tee_step.sh log/wf_main.log comando arg...
set -u
log=$1
shift
mkdir -p "$(dirname "$log")"
printf '\n===== %s' "$(date -Is)" >> "$log"
printf ' %s' "$@" >> "$log"
printf ' =====\n' >> "$log"
part=$(mktemp)
set +e
"$@" >"$part" 2>&1
rc=$?
cat "$part" | tee -a "$log"
rm -f "$part"
exit "$rc"
