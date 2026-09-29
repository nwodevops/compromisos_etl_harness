# CHECKPOINTS — arquetipo mínimo

Criterios para marcar features `done` en [`feature_list.json`](feature_list.json).  
Verificación de humo: [`./init.sh`](init.sh) (`HARNESS OK`).  
Verificación de datos: [`scripts/control_datos.py`](scripts/control_datos.py). No resetea H2.  
`HARNESS OK` no cierra las fases 2 ni 3.

---

## Global

- [ ] `./init.sh` termina con **`HARNESS OK`**.
- [ ] Sin passwords reales en `project-config.json` / `environments/`.
- [ ] Log sin literales `${VAR}`.
- [ ] Un solo `.py` en `logica/`.
- [ ] Máximo **una** feature `in_progress`.

---

## Fase 1 — Entorno {#fase-1}

- [ ] H2 levanta en puerto 9092 (`reset_and_create.sh`).
- [ ] `python/create_stg.py` OK (puede ser no-op con `sources: []`).
- [ ] `python/main.py` OK con `logica/compromisos.py`.
- [ ] `wf_main.hwf` ejecutable en Hop GUI.

---

## Fase 2 — Fuentes STG {#fase-2}

- [ ] Al menos una fuente en `inputs.yaml`.
- [ ] Tabla `STG_*` creada en H2.
- [ ] Pipeline `pl_stage_*.hpl` cableado en `wf_main.hwf`.
- [ ] Hop carga filas en STG (conteo > 0 en log).
- [ ] `progress/impl_fase-2-fuentes-stg.md` trae el conteo de filas por `COD_FUENTE` en cada `STG_*`, y la lista de libros que fallaron (403 o pestaña ausente). `HARNESS OK` solo no cierra esta fase.
- [ ] La primera fila de datos de cada libro accesible está en las tres tablas. Sentinelas: `CMIN`/`REU001` y `AMAZONAS`/`REU_AMA001`. `scripts/control_datos.py` termina en `CONTROL OK`.

Ver skill `hop-python-etl` e [`inputs.example.yaml`](.agents/skills/hop-python-etl/inputs.example.yaml).

---

## Fase 3 — Lógica {#fase-3}

- [ ] Claves STG en `python/io/leer_h2.py`.
- [ ] `logica/<tu_logica>.py` produce `RESULTADO` con filas > 0.
- [ ] `output/resultado.xlsx` generado (si se usa salida Excel).
- [ ] `progress/impl_fase-3-logica.md` lista, por cada tabla de salida, los encabezados que se apilaron y los que quedaron en campos distintos.
- [ ] Oracle y MySQL tienen el mismo número de filas en `DW_ACU_REUNIONES`, `DW_ACU_BASE_ACUERDOS` y `DW_ACU_DATOS`.

Contrato: [`python/CONTRATO.md`](python/CONTRATO.md).

---

## Fuera de alcance del cascarón

- Modelo dimensional Oracle (`cargar_dw.py`) → copiar cuando el proyecto lo pida.
- Fases Kimball / indicadores → no vienen en esta plantilla.
