# Verificación — arquetipo mínimo

## Automática

```bash
chmod +x init.sh
./init.sh   # HARNESS OK
```

Comprueba: H2, `create_stg.py`, `main.py`, salida `RESULTADO`, sin `${VAR}` literal.

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
