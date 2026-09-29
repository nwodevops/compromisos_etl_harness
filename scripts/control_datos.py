#!/usr/bin/env python3
"""Control de datos después de una corrida. No resetea H2 ni escribe en las bases.

En este proyecto (hay docs/inputs/fuentes_sheets.json) compara Oracle y MySQL
y exige las primeras filas que Hop no debe perder. En un arquetipo nuevo, sin
ese catálogo, termina en 0 con un aviso.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "python"))

from config import load_vars, require_live_conn  # noqa: E402

TABLAS = (
    "DW_ACU_REUNIONES",
    "DW_ACU_BASE_ACUERDOS",
    "DW_ACU_DATOS",
)
SENTINELAS = (
    ("CMIN", "REU001"),
    ("AMAZONAS", "REU_AMA001"),
)


def _libros_sin_acceso(catalog: dict) -> list[str]:
    lineas = []
    for familia, bloque in catalog.items():
        if not isinstance(bloque, dict):
            continue
        for libro in bloque.get("libros") or []:
            acceso = libro.get("acceso")
            if acceso:
                lineas.append(f"{familia} {libro.get('cod')}: {acceso}")
    return lineas


def _mysql_counts(variables: dict) -> dict[str, dict]:
    import mysql.connector

    cv = require_live_conn("mysql_dw", variables)
    port = int(cv["port"]) if str(cv["port"]).isdigit() else 3306
    conn = mysql.connector.connect(
        host=cv["host"],
        port=port,
        user=cv["username"],
        password=cv["password"],
        database=cv["database"],
        charset="utf8mb4",
    )
    out: dict[str, dict] = {}
    try:
        cur = conn.cursor()
        for tabla in TABLAS:
            cur.execute(f"SELECT COUNT(*) FROM `{tabla}`")
            total = int(cur.fetchone()[0])
            claves = {}
            for fuente, reunion in SENTINELAS:
                cur.execute(
                    f"SELECT COUNT(*) FROM `{tabla}` "
                    "WHERE COD_FUENTE=%s AND COD_REUNION=%s",
                    (fuente, reunion),
                )
                claves[(fuente, reunion)] = int(cur.fetchone()[0])
            out[tabla] = {"total": total, "claves": claves}
    finally:
        conn.close()
    return out


def _oracle_counts(variables: dict) -> dict[str, dict]:
    import oracledb

    cv = require_live_conn("oracle_dw", variables)
    dsn = f"{cv['host']}:{cv['port']}/{cv['database']}"
    conn = oracledb.connect(user=cv["username"], password=cv["password"], dsn=dsn)
    out: dict[str, dict] = {}
    try:
        cur = conn.cursor()
        for tabla in TABLAS:
            cur.execute(f"SELECT COUNT(*) FROM {tabla}")
            total = int(cur.fetchone()[0])
            claves = {}
            for fuente, reunion in SENTINELAS:
                cur.execute(
                    f"SELECT COUNT(*) FROM {tabla} "
                    "WHERE COD_FUENTE = :f "
                    "AND DBMS_LOB.SUBSTR(COD_REUNION, 200, 1) = :r",
                    {"f": fuente, "r": reunion},
                )
                claves[(fuente, reunion)] = int(cur.fetchone()[0])
            out[tabla] = {"total": total, "claves": claves}
    finally:
        conn.close()
    return out


def main() -> int:
    catalogo = ROOT / "docs" / "inputs" / "fuentes_sheets.json"
    if not catalogo.is_file():
        print("AVISO: sin catálogo de Sheets ni sentinelas; control de datos en espera")
        return 0

    catalog = json.loads(catalogo.read_text(encoding="utf-8"))
    print("LIBROS SIN ACCESO (no cuentan como carga exitosa)")
    sin_acceso = _libros_sin_acceso(catalog)
    if sin_acceso:
        for linea in sin_acceso:
            print(f"  {linea}")
    else:
        print("  (ninguno)")

    variables = load_vars(ROOT)
    try:
        mysql = _mysql_counts(variables)
        oracle = _oracle_counts(variables)
    except Exception as exc:
        print(f"FAIL: no se pudo leer Oracle o MySQL ({exc})", file=sys.stderr)
        return 1

    errores: list[str] = []
    for tabla in TABLAS:
        n_my = mysql[tabla]["total"]
        n_ora = oracle[tabla]["total"]
        print(f"{tabla}: mysql={n_my} oracle={n_ora}")
        if n_my != n_ora:
            errores.append(f"{tabla}: mysql {n_my} != oracle {n_ora}")
        for fuente, reunion in SENTINELAS:
            c_my = mysql[tabla]["claves"][(fuente, reunion)]
            c_ora = oracle[tabla]["claves"][(fuente, reunion)]
            marca = "ok" if c_my and c_ora else "FALTA"
            print(f"  {marca} {fuente} {reunion}: mysql={c_my} oracle={c_ora}")
            if c_my < 1 or c_ora < 1:
                errores.append(f"{tabla} sin {fuente}/{reunion}")

    if errores:
        print("FAIL control de datos:", file=sys.stderr)
        for item in errores:
            print(f"  {item}", file=sys.stderr)
        return 1
    print("CONTROL OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
