# impl fase-3-logica

Fecha: 2026-09-26

## Archivos

- `logica/compromisos.py` (se borró `logica/demo.py`)
- `python/io/leer_h2.py`, `python/main.py`, `python/io/escribir_excel.py`
- `python/CONTRATO.md`
- `output/resultado.xlsx`

## Salida

- Reuniones: 265 filas
- Base Acuerdos: 878 filas
- Datos adicionales: 805 filas
- Conteos: 73 filas

## Encabezados

Apilados en Reuniones: ADM, AGENDA, COD_ACCION, COD_REUNION, COMENTARIOS, EXIST_ACUERDOS, FEC_REUNION, HORAF_REUNION, HORAI_REUNION, LUGAR_REUNION, NRO_EXPEDIENTE, SOL_REUNION, TIPO_DOC, UF

Solo sede: CANT_ACUERDOS. Solo OD: AUX.

Base Acuerdos: las 19 columnas de código se apilaron. Ninguna quedó solo en una familia.

Datos adicionales: las 26 columnas de código se apilaron. Ninguna quedó solo en una familia.

## ./init.sh

`HARNESS OK`. El smoke deja H2 vacío. El Excel con filas se restauró después del smoke.
