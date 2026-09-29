# Verificación — arquetipo mínimo

## Automática

```bash
chmod +x init.sh
./init.sh   # HARNESS OK
```

Comprueba el humo: H2, `create_stg.py`, `main.py`, salida `RESULTADO`, sin `${VAR}` literal.
Si H2 ya tiene filas `STG_*`, `./init.sh` no resetea. Para vaciar: `INIT_FORCE=1 ./init.sh`.

Datos, sin reset:

```bash
.venv/bin/python scripts/control_datos.py   # CONTROL OK
```

Comprueba que Oracle y MySQL tengan las mismas filas en `DW_ACU_*` y que existan `CMIN`/`REU001` y `AMAZONAS`/`REU_AMA001`. Los libros en 403 se listan y no cuentan como éxito. `HARNESS OK` no cierra las fases 2, 3 ni 4. La fase 4 pide además `PK_OFICINA`: `CMIN` = `COR064`, `AMAZONAS` = `COR047`, `CHIMBOTE` = `COR033`, con el mismo conteo no nulo en Oracle y MySQL.

## Manual Hop

Play [`workflows/wf_main.hwf`](workflows/wf_main.hwf) en Apache Hop GUI.

## Manual Python

```bash
.venv/bin/python python/main.py
# → output/resultado.xlsx
```

## Tras añadir fuentes (Fase 2)

1. Entradas en `inputs.yaml`
2. `pl_stage_*.hpl` cableado en `wf_main.hwf`
3. `./init.sh` o corrida Hop con conteos STG > 0
