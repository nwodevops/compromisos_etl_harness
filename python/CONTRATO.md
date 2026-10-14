# Contrato logica/ (acuerdos)

## Flujo

```
python/main.py
  → io/leer_h2.py     (H2 → DataFrames)
  → logica/compromisos.py
  → io/oficinas.py         (TX_OFICINA y PK_OFICINA)
  → io/escribir_excel.py   (output/resultado.xlsx, 4 hojas)
  → io/cargar_acu.py      (Oracle y MySQL: DW_ACU_*)
```

## Entrada

Claves de `LECTURAS` en `python/io/leer_h2.py`:

| Clave | Tabla |
|---|---|
| `SEDE_REUNIONES` | `STG_SEDE_REUNIONES` |
| `SEDE_ACUERDOS` | `STG_SEDE_ACUERDOS` |
| `SEDE_DATOS` | `STG_SEDE_DATOS` |
| `OD_REUNIONES` | `STG_OD_REUNIONES` |
| `OD_ACUERDOS` | `STG_OD_ACUERDOS` |
| `OD_DATOS` | `STG_OD_DATOS` |

## Salida

| Nombre | Hoja Excel | Descripción |
|---|---|---|
| `DF_REUNIONES` | Reuniones | Sede + OD apilados |
| `DF_BASE_ACUERDOS` | Base Acuerdos | Sede + OD apilados |
| `DF_DATOS_ADICIONALES` | Datos adicionales | Sede + OD apilados |
| `RESULTADO` | Conteos | Filas por tabla, familia y código |

Apilado: igualdad del encabezado después de recortar, colapsar espacios, pasar a minúsculas y quitar tildes. Un nombre distinto queda en su propio campo. `FAMILIA` y `COD_FUENTE` van al inicio. Orden: `FAMILIA`, `COD_FUENTE`.

`io/oficinas.py` agrega `TX_OFICINA` y `PK_OFICINA` (`VARCHAR(20)` / `VARCHAR2(20)`) después de `COD_FUENTE`. El cruce está en `docs/inputs/oficinas.yaml` y en `T_SEP_OFICINA`. Sin coincidencia, `PK_OFICINA` queda vacío y la carga sigue.

## Reglas

- Un solo `.py` en `logica/`.
- Sin conexiones ni drivers en `logica/` (I/O en `python/io/`).
- `pandas` inyectado como `pd`.
- Valores: se recortan espacios y el texto `nan` queda vacío. Tokens de celda completa (`NO APLICA`, `SI`, `NO`, `TRUE`, `FALSE`) salen en una sola grafía. En `HUMANOS`, `FLORA`, `FAUNA`, `AGUA`, `AIRE` y `SUELO`, `0`/`1` pasan a `FALSE`/`TRUE`. Las columnas de estado no se fusionan.
