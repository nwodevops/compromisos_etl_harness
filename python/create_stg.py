#!/usr/bin/env python3
"""Crea tablas STG_* en H2 a partir de inputs.yaml. No extrae filas.

Lo llama Hop (acción Shell previa al stage) o el harness antes de cargar datos.
CAPA STG/DDL — no importar python/io ni logica/.

Flujo:
  inputs.yaml → introspect (oracle|sheets|excel) → CREATE TABLE STG_* en H2

Uso (H2 ya levantado tras Reset):
  .venv/bin/python python/create_stg.py

sources: [] -> no-op exit 0 (smoke test del arquetipo).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from config import load_sources, load_vars, project_root, require_live_conn  # noqa: E402
from introspect import excel, oracle, sheets  # noqa: E402
from introspect.h2_ddl import apply_h2, create_table_sql, write_script  # noqa: E402

# type en inputs.yaml → función que deduce columnas del origen
HANDLERS = {
    "oracle": oracle.introspect,
    "sheets": sheets.introspect,
    "excel": excel.introspect,
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Genera y aplica DDL STG_* en H2")
    parser.add_argument(
        "--root",
        default=None,
        help="Raíz del proyecto Hop (default: padre de python/)",
    )
    args = parser.parse_args(argv)

    root = Path(args.root).resolve() if args.root else project_root()
    variables = load_vars(root)
    sources = load_sources(root, variables)

    if not sources:
        out = write_script(root, [])
        print(f"sources: [] -> no-op. Escrito {out.relative_to(root)}")
        return 0

    statements: list[tuple[str, str]] = []
    for src in sources:
        typ = src["type"]
        stg = src["stg_table"]
        handler = HANDLERS.get(typ)
        if handler is None:
            raise SystemExit(
                f"{stg}: type {typ!r} desconocido. Usa: {', '.join(HANDLERS)}"
            )
        if typ in ("oracle", "sheets"):
            conn_name = src.get("connection") or (
                "oracle_sisud" if typ == "oracle" else None
            )
            if conn_name:
                require_live_conn(conn_name, variables)
        cols = handler(src, variables, root)
        sql = create_table_sql(stg, cols)
        statements.append((stg, sql))
        print(f"{stg}: {len(cols)} columnas ({typ})")

    out = write_script(root, statements)
    print(f"escrito: {out.relative_to(root)}")
    apply_h2(root, variables, statements)
    print(f"aplicado H2: {len(statements)} tablas")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (FileNotFoundError, ValueError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
