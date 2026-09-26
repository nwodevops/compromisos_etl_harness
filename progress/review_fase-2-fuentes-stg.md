# review fase-2-fuentes-stg

Contra CHECKPOINTS.md#fase-2.

- `inputs.yaml` tiene 6 fuentes sheets.
- `create_stg.py` creó las 6 `STG_*` (16, 20 y 27 columnas).
- `pl_stage_*.hpl` existen y `wf_main.hwf` llama a `python/stage_sheets.py`, que ejecuta Hop.
- Hay filas en STG. El detalle por `COD_FUENTE` y los fallos están en `progress/impl_fase-2-fuentes-stg.md`.
- `HARNESS OK` no se usó como único cierre.

Pasa. Los 8 libros de sede en 403 siguen fuera hasta que se compartan.
