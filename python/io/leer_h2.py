"""ENTRADA post-staging: H2 -> pandas DataFrames.

Claves = nombres inyectados en logica/. Ampliar al añadir STG_*.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from h2_conn import connect_h2

LECTURAS: dict[str, str] = {
    "SEDE_REUNIONES": "SELECT * FROM PUBLIC.STG_SEDE_REUNIONES",
    "SEDE_ACUERDOS": "SELECT * FROM PUBLIC.STG_SEDE_ACUERDOS",
    "SEDE_DATOS": "SELECT * FROM PUBLIC.STG_SEDE_DATOS",
    "OD_REUNIONES": "SELECT * FROM PUBLIC.STG_OD_REUNIONES",
    "OD_ACUERDOS": "SELECT * FROM PUBLIC.STG_OD_ACUERDOS",
    "OD_DATOS": "SELECT * FROM PUBLIC.STG_OD_DATOS",
}


def _coerce_dates(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in out.columns:
        if pd.api.types.is_datetime64_any_dtype(out[col]):
            out[col] = pd.to_datetime(out[col]).dt.date
    return out


def leer_h2(root: Path, variables: dict[str, str]) -> dict[str, pd.DataFrame]:
    if not LECTURAS:
        raise ValueError("LECTURAS vacío; agrega queries en python/io/leer_h2.py")

    conn = connect_h2(root, variables)
    datos: dict[str, pd.DataFrame] = {}
    try:
        cur = conn.cursor()
        try:
            for nombre, query in LECTURAS.items():
                try:
                    cur.execute(query)
                except Exception as exc:
                    msg = str(exc).split("\n")[0][:120]
                    print(f"AVISO: {nombre} no disponible ({msg}); DataFrame vacío")
                    datos[nombre] = pd.DataFrame()
                    continue
                cols = [d[0] for d in cur.description]
                rows = cur.fetchall()
                df = pd.DataFrame.from_records(rows, columns=cols)
                datos[nombre] = _coerce_dates(df)
                print(f"{nombre}: {len(datos[nombre])} x {len(datos[nombre].columns)}")
        finally:
            cur.close()
    finally:
        conn.close()
    return datos
