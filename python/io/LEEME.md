# python/io/ — I/O post-staging (arquetipo mínimo)

Hop (o el smoke) deja datos en H2. Aquí se lee H2 y se escribe el destino demo.

Flujo en `main.py`:
  `leer_h2.py` → `logica/` → `escribir_excel.py` → `output/resultado.xlsx`

- `leer_h2.py` — `LECTURAS` (contrato de entrada de `logica/`)
- `escribir_excel.py` — salida Excel del smoke / MVP

Cuando el ETL pase a DW Oracle, añade `cargar_dw.py` (wipe+DDL+INSERT) y cambia
`main.py` para usarlo; no hace falta Excel en producción.

No crear `STG_*` aquí. Eso es `python/create_stg.py` / `introspect/`.

No importar este paquete como `import io`: choca con la stdlib.
