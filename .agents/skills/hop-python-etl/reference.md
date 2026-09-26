# Referencia — staging H2 y tipos

Ver [SKILL.md](SKILL.md) para arquitectura.

## Introspección (`python/create_stg.py`)

Reset H2 primero; Python lee `inputs.yaml`, introspecta, escribe `h2/sql/02_stg.sql` (gitignore) y aplica JDBC.

| type | Conexión | object |
|---|---|---|
| oracle | `DB_ORA_SISUD_*` | `OWNER.NOMBRE` |
| sheets | `client_secret.json` | `spreadsheet_key` + `worksheet` |
| excel | path relativo | `worksheet` + `header_row` (1-based) |

Sheets/Excel: **todos VARCHAR** (gotcha `#N/A`). Landing: nullable, sin PK.

`sources: []` → no-op (smoke del cascarón; queda `DEMO_TABLA_EJEMPLO`).

## Convención `STG_*`

| Origen | Prefijo |
|---|---|
| Oracle | `STG_ORA_` |
| Sheets libro N | `STG_GSN_` |
| Excel | `STG_XLS_` o el prefijo que acuerdes |

Una fuente = una tabla STG. No UNION en H2.

## Orden wf_main

```
Reset H2 → Python create STG → pl_stage_* → Run Python → Success
```

Python create STG va **antes** de los pipelines de extract (in-memory se borra en reset).

## Capa post-staging

- Lectura: `python/io/leer_h2.py` → `LECTURAS`
- Escritura demo: `python/io/escribir_excel.py` → `output/resultado.xlsx`

## Debug rápido

| Síntoma | Revisar |
|---|---|
| STG en 0 filas | Hop staging omitido (credenciales `<...>`) o pipeline no cableado |
| Lógica no ve tabla | Falta clave en `LECTURAS` |
| `Value too long` en H2 | VARCHAR con longitud; quitar longitud en DDL |
