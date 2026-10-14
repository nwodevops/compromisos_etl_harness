# python/ — tres capas

Hop llama estos scripts. No mezclar reglas de negocio con conexiones.

| Capa | Cuándo | Entry | Carpeta | Hace | No hace |
|---|---|---|---|---|---|
| DDL | Antes del extract | `create_stg.py` | `introspect/` | Lee `inputs.yaml`, `CREATE TABLE STG_*` | Extraer filas, reglas |
| Extract | Después del DDL | `stage/stage_sheets.py` | `stage/` | Hop baja Sheets a `STG_*` | Reglas de negocio |
| Post-staging | Después de la carga | `main.py` | `io/` + `logica/` | Lee H2, transforma, Excel y `DW_ACU_*` | Introspectar fuentes |

```
inputs.yaml  →  create_stg.py  →  introspect/          →  H2 tablas vacías
stage/       →  Hop pl_stage    →  STG_* con filas
main.py      →  io/leer_h2      →  logica/*.py
             →  io/escribir_excel + io/cargar_acu
```

`config.py` y `h2_conn.py` son compartidos (variables Hop + JDBC H2).

`logica/` no abre conexiones. `io/` no llama a `introspect/`.

La corrida Hop deja copia en `log/wf_main.log` y `log/wf_create_stg.log`.

Contrato: [`CONTRATO.md`](CONTRATO.md).
