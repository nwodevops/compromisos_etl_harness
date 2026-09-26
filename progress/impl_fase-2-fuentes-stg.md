# impl fase-2-fuentes-stg

Fecha: 2026-09-26

## Archivos

- `docs/inputs/fuentes_sheets.json`
- `inputs.yaml`
- `python/fuentes_catalog.py`, `python/freeze_fuentes.py`, `python/hop_sheet.py`, `python/stage_sheets.py`
- `python/introspect/sheets.py`
- `pipelines/pl_stage_{sede,od}_{reuniones,acuerdos,datos}.hpl`
- `workflows/wf_main.hwf` (Stage sheets)

Hop es posicional. Cada libro genera un `.hpl` en `pipelines/.run/` con las columnas en el orden de su fila de códigos. `COD_FUENTE` se rellena después.

## Libros sin acceso (403)

No compartidos con la cuenta de servicio:

- sede CHID, CELE, CIND, CPES, CAGR, CRES, UFED, UFSAVC

Sede cargada: CMIN.

## Hojas sin filas

Hop devuelve `values is null` cuando bajo el encabezado no hay datos:

- Reuniones y Base Acuerdos: ANCASH, APURIMAC, AYACUCHO, HUANCAVELICA, PASCO, COTABAMBAS, ESPINAR

En Datos adicionales esas mismas oficinas solo traían casillas `FALSE`. Esas filas se quitaron.

## Conteos por COD_FUENTE

STG_SEDE_REUNIONES: CMIN 1

STG_SEDE_ACUERDOS: CMIN 4

STG_SEDE_DATOS: CMIN 4

STG_OD_REUNIONES: AMAZONAS 23, AREQUIPA 25, CAJAMARCA 7, CHIMBOTE 2, CORACORA 3, CUSCO 5, HUANUCO 1, ICA 13, JUNIN 30, LA LIBERTAD 20, LAMBAYEQUE 16, LORETO 1, MADRE DE DIOS 6, MOQUEGUA 7, PICHANAKI 13, PIURA 20, PUNO 12, SAN MARTIN 26, TACNA 6, TALARA 6, TUMBES 9, UCAYALI 13

STG_OD_ACUERDOS: AMAZONAS 66, AREQUIPA 86, CAJAMARCA 29, CHIMBOTE 10, CORACORA 9, CUSCO 6, HUANUCO 6, ICA 36, JUNIN 86, LA CONVENCION 2, LA LIBERTAD 60, LAMBAYEQUE 79, LORETO 4, MADRE DE DIOS 19, MOQUEGUA 18, PICHANAKI 38, PIURA 62, PUNO 40, SAN MARTIN 90, TACNA 14, TALARA 22, TUMBES 35, UCAYALI 56, VRAEM 1

STG_OD_DATOS (sin filas que solo tenían FALSE): AMAZONAS 42, AREQUIPA 64, CAJAMARCA 28, CHIMBOTE 10, CORACORA 9, CUSCO 12, HUANUCO 6, ICA 36, JUNIN 66, LA CONVENCION 2, LA LIBERTAD 60, LAMBAYEQUE 79, LORETO 4, MADRE DE DIOS 19, MOQUEGUA 18, PICHANAKI 38, PIURA 62, PUNO 40, SAN MARTIN 87, TACNA 14, TALARA 21, TUMBES 30, UCAYALI 53, VRAEM 1

## ./init.sh

`HARNESS OK` al cerrar la fase 3 (el smoke resetea H2). `logica/demo.py` se reemplazó en la fase 3.
