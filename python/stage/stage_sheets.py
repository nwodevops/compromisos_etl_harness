#!/usr/bin/env python3
"""Carga Google Sheets → H2 STG_* con Hop.

Por cada libro reescribe el pipeline: GoogleSheetsInput es posicional,
y el orden de columnas no es el mismo en todos los libros. El nombre
de cada campo es el de la fila de códigos, así TableOutput cae en la
columna STG correcta. COD_FUENTE se rellena después, donde quedó nulo.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
PY = HERE.parent
if str(PY) not in sys.path:
    sys.path.insert(0, str(PY))

from config import load_vars, project_root  # noqa: E402
from h2_conn import connect_h2  # noqa: E402
from introspect.h2_ddl import sanitize_ident  # noqa: E402
from stage.fuentes_catalog import PESTANAS, load_catalog, norm_header  # noqa: E402
from stage.hop_sheet import write_pipeline  # noqa: E402

RETRIES = 3
RETRY_SLEEP = 8


def hop_run() -> str:
    """hop-run del mismo Hop que informes: HOP_RUN, HOP_HOME, D:\\Eder\\hop, ~/apps/hop."""
    env = os.environ.get("HOP_RUN")
    if env and os.path.isfile(env):
        return env
    if sys.platform.startswith("win"):
        names = ("hop-run.bat", "hop-run.cmd", "hop-run.sh")
    else:
        names = ("hop-run.sh", "hop-run.bat", "hop-run.cmd")
    roots: list[Path] = []
    hop_home = os.environ.get("HOP_HOME")
    if hop_home:
        roots.append(Path(hop_home))
    roots.append(Path(r"D:\Eder\hop"))
    roots.append(Path.home() / "apps" / "hop")
    for root in roots:
        for name in names:
            candidate = root / name
            if candidate.is_file():
                return str(candidate)
    raise SystemExit("no se encontró hop-run (define HOP_RUN)")


def hop_cmd(hop: str, root: Path, pipeline: Path) -> list[str]:
    args = ["-j", root.name, "-f", str(pipeline), "-r", "local"]
    if hop.lower().endswith((".bat", ".cmd")):
        return ["cmd", "/c", hop, *args]
    return [hop, *args]


def ident_por_norma(columnas: list[str]) -> dict[str, str]:
    """Misma sanitización que create_stg, en el orden del catálogo."""
    used: set[str] = set()
    sanitize_ident("COD_FUENTE", used)
    out: dict[str, str] = {}
    for col in columnas:
        key = norm_header(col)
        if not key or key in out:
            continue
        out[key] = sanitize_ident(col, used)
    return out


def vaciar(root: Path, variables: dict[str, str], tables: list[str]) -> None:
    conn = connect_h2(root, variables)
    try:
        cur = conn.cursor()
        for table in tables:
            cur.execute(f"TRUNCATE TABLE PUBLIC.{table}")
        conn.commit()
        print("TRUNCATED " + ", ".join(tables))
    finally:
        conn.close()


def borrar_vacias(
    root: Path, variables: dict[str, str], table: str, idents: list[str]
) -> None:
    """Quita filas en blanco y las que solo traen FALSE de casillas."""
    if not idents:
        return
    todas = " AND ".join(f'"{col}" IS NULL' for col in idents)
    sqls = [f'DELETE FROM PUBLIC.{table} WHERE "COD_FUENTE" IS NULL AND {todas}']
    if "COD_REUNION" in idents:
        sqls.append(
            f'DELETE FROM PUBLIC.{table} WHERE "COD_FUENTE" IS NULL AND "COD_REUNION" IS NULL'
        )
    conn = connect_h2(root, variables)
    try:
        cur = conn.cursor()
        for sql in sqls:
            cur.execute(sql)
        conn.commit()
    finally:
        conn.close()


def marcar_fuente(
    root: Path, variables: dict[str, str], table: str, cod: str
) -> int:
    conn = connect_h2(root, variables)
    try:
        cur = conn.cursor()
        cur.execute(
            f'UPDATE PUBLIC.{table} SET "COD_FUENTE" = ? WHERE "COD_FUENTE" IS NULL',
            [cod],
        )
        conn.commit()
        return int(cur.rowcount)
    finally:
        conn.close()


def correr_hop(hop: str, root: Path, pipeline: Path, label: str) -> str:
    """Devuelve 'ok' o 'vacia'. Una hoja sin filas hace fallar a Hop con values=null."""
    cmd = hop_cmd(hop, root, pipeline)
    attempt = 1
    while True:
        proc = subprocess.run(cmd, cwd=str(root), capture_output=True, text=True)
        sys.stdout.write(proc.stdout)
        sys.stderr.write(proc.stderr)
        blob = proc.stdout + proc.stderr
        if proc.returncode == 0:
            return "ok"
        if "values" in blob and "null" in blob:
            print(f"SIN_FILAS: {label}")
            return "vacia"
        if attempt >= RETRIES:
            print(f"FAIL: {label} tras {RETRIES} intentos (rc={proc.returncode})")
            raise SystemExit(proc.returncode)
        print(f"AVISO: {label} fallo (rc={proc.returncode}); reintento {attempt}/{RETRIES}")
        time.sleep(RETRY_SLEEP)
        attempt += 1


def conteos(root: Path, variables: dict[str, str], tables: list[str]) -> None:
    conn = connect_h2(root, variables)
    try:
        cur = conn.cursor()
        for table in tables:
            cur.execute(
                f'SELECT "COD_FUENTE", COUNT(*) FROM PUBLIC.{table} '
                f'GROUP BY "COD_FUENTE" ORDER BY "COD_FUENTE"'
            )
            rows = cur.fetchall()
            print(f"CONTEO {table}")
            if not rows:
                print("  (vacía)")
            for cod, n in rows:
                print(f"  {cod}: {n}")
    finally:
        conn.close()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--solo", default="", help="COD_FUENTE a cargar, para prueba")
    args = parser.parse_args()

    root = project_root()
    if not (root / "client_secret.json").is_file():
        raise SystemExit("FAIL: falta client_secret.json")
    variables = load_vars(root)
    catalog = load_catalog(root)
    hop = hop_run()
    run_dir = root / "pipelines" / ".run"
    credential = root / "client_secret.json"

    tables: list[str] = []
    for familia in ("sede", "od"):
        for pestana in PESTANAS:
            tables.append(catalog[familia]["pestanas"][pestana["id"]]["stg_table"])
    if not args.solo:
        vaciar(root, variables, tables)

    fallos: list[str] = []
    for familia in ("sede", "od"):
        fam = catalog[familia]
        libros = [b for b in fam.get("libros") or [] if b.get("activo", True)]
        if args.solo:
            libros = [b for b in libros if b.get("cod") == args.solo]
        for n, libro in enumerate(libros, start=1):
            cod = libro["cod"]
            if libro.get("acceso"):
                msg = f"{familia} {cod}: acceso {libro['acceso']}"
                print(f"FAIL {msg}")
                fallos.append(msg)
                continue
            for pestana in PESTANAS:
                spec = (libro.get("pestanas") or {}).get(pestana["id"]) or {}
                meta = fam["pestanas"][pestana["id"]]
                table = meta["stg_table"]
                if spec.get("error") or not spec.get("columns"):
                    msg = f"{familia} {cod} {pestana['worksheet']}: {spec.get('error', 'sin columnas')}"
                    print(f"FAIL {msg}")
                    fallos.append(msg)
                    continue
                mapa = ident_por_norma(meta["columns"])
                columnas = []
                desconocida = False
                for raw in spec["columns"]:
                    ident = mapa.get(norm_header(raw))
                    if not ident:
                        msg = f"{familia} {cod} {pestana['worksheet']}: columna fuera del catálogo {raw}"
                        print(f"FAIL {msg}")
                        fallos.append(msg)
                        desconocida = True
                        break
                    columnas.append(ident)
                if desconocida:
                    continue
                # Hop no escribe la primera fila del rango. Esa fila es la de códigos.
                data_row = int(spec["header_row"])
                hpl = run_dir / f"{table}_{cod.replace(' ', '_')}.hpl"
                write_pipeline(
                    hpl,
                    name=hpl.stem,
                    spreadsheet_key=libro["spreadsheet_key"],
                    worksheet=pestana["worksheet"],
                    data_row=data_row,
                    columns=columnas,
                    table=table,
                    credential=credential,
                )
                label = f"[{n}/{len(libros)}] {familia} {cod} {pestana['worksheet']}"
                print(f"==> {label}")
                try:
                    estado = correr_hop(hop, root, hpl, label)
                except SystemExit:
                    fallos.append(label)
                    continue
                if estado == "vacia":
                    fallos.append(f"{label}: sin filas")
                    continue
                idents = [mapa[norm_header(c)] for c in meta["columns"]]
                borrar_vacias(root, variables, table, idents)
                filas = marcar_fuente(root, variables, table, cod)
                print(f"filas={filas}")

    print("--- FALLIDOS ---")
    if fallos:
        for item in fallos:
            print(item)
    else:
        print("(ninguno)")
    conteos(root, variables, tables)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
