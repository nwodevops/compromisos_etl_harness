# review fase-1-entorno

Contra CHECKPOINTS.md#fase-1.

- H2 en puerto 9092: sí (`H2 OK puerto 9092`).
- `python/create_stg.py` con `sources: []`: sí, no-op.
- `python/main.py` con `logica/demo.py`: sí, `RESULTADO` 2 filas.
- `wf_main.hwf` presente y sin cambios en esta fase.
- `./init.sh` termina en `HARNESS OK`.
- Una sola feature `in_progress`.

Pasa.
