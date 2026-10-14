#!/usr/bin/env python3
"""Arma docs/inputs/fuentes_sheets.json desde input/input_excel/test.txt.

Lee solo las primeras filas de cada pestaña para ubicar la fila de códigos.
Con --probe usa un JSON ya descargado (misma forma que el sondeo).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent
PY = HERE.parent
if str(PY) not in sys.path:
    sys.path.insert(0, str(PY))

from stage.fuentes_catalog import PESTANAS, code_header, union_columns  # noqa: E402

ROOT = PY.parent


def _strip_accents(text: str) -> str:
    text = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in text if unicodedata.category(ch) != "Mn")


def parse_test(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8")
    sede_txt, _, od_txt = text.partition("#####")
    libros: list[dict] = []
    for line in sede_txt.splitlines():
        line = line.strip()
        if not line or ":" not in line or line.lower().startswith("sede"):
            continue
        nombre, key = line.split(":", 1)
        key = key.strip()
        if not key:
            continue
        cod = nombre.strip().split("-")[-1].strip().upper().replace(" ", "")
        libros.append(
            {
                "familia": "sede",
                "cod": cod,
                "nombre": nombre.strip(),
                "spreadsheet_key": key,
                "activo": True,
            }
        )
    for match in re.finditer(r"\*\*(.+?)\*\*\s*:\s*`([^`]+)`", od_txt):
        nombre = re.sub(r"\s+", " ", match.group(1)).strip()
        cod_match = re.search(r"\bOD\s+(.+)$", nombre, flags=re.I)
        if not cod_match:
            raise SystemExit(f"sin código OD en {nombre!r}")
        cod = _strip_accents(cod_match.group(1)).upper().strip()
        libros.append(
            {
                "familia": "od",
                "cod": cod,
                "nombre": nombre,
                "spreadsheet_key": match.group(2).strip(),
                "activo": True,
            }
        )
    return libros


def _probe_index(path: Path) -> dict[str, dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return {item["spreadsheet_key"]: item for item in data}


def _live_rows(key: str, worksheets: list[str]) -> dict:
    import gspread
    from gspread.exceptions import APIError, WorksheetNotFound

    gc = gspread.service_account(filename=str(ROOT / "client_secret.json"))
    try:
        book = gc.open_by_key(key)
    except APIError as exc:
        status = getattr(getattr(exc, "response", None), "status_code", None)
        return {"error": status or "api", "msg": str(exc)[:180]}
    tabs: dict[str, list] = {}
    for name in worksheets:
        try:
            tabs[name] = book.worksheet(name).get("A1:AZ5")
        except WorksheetNotFound:
            tabs[name] = []
        time.sleep(0.2)
    return {"tabs": tabs}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--probe", default="", help="JSON de sondeo ya descargado")
    args = parser.parse_args(argv)

    libros = parse_test(ROOT / "input" / "input_excel" / "test.txt")
    probe = _probe_index(Path(args.probe)) if args.probe else {}
    worksheets = [p["worksheet"] for p in PESTANAS]
    enriched: list[dict] = []
    for i, libro in enumerate(libros, start=1):
        item = dict(libro)
        item["pestanas"] = {}
        if probe:
            src = probe.get(libro["spreadsheet_key"], {})
            if src.get("error"):
                item["acceso"] = str(src["error"].get("_error", "error"))
            payload = {"tabs": src.get("tabs") or {}}
        else:
            payload = _live_rows(libro["spreadsheet_key"], worksheets)
            if payload.get("error"):
                item["acceso"] = str(payload["error"])
        if item.get("acceso"):
            print(f"FAIL {i}/{len(libros)} {libro['familia']} {libro['cod']} {item['acceso']}")
            enriched.append(item)
            continue
        for pestana in PESTANAS:
            rows = (payload.get("tabs") or {}).get(pestana["worksheet"]) or []
            if not rows:
                item["pestanas"][pestana["id"]] = {"error": "pestaña ausente"}
                continue
            found = code_header(rows)
            if not found:
                item["pestanas"][pestana["id"]] = {"error": "sin fila de códigos"}
                continue
            header_row, columns = found
            item["pestanas"][pestana["id"]] = {
                "header_row": header_row,
                "columns": columns,
            }
        print(f"OK {i}/{len(libros)} {libro['familia']} {libro['cod']}")
        enriched.append(item)

    catalog: dict = {}
    for familia in ("sede", "od"):
        pestanas_out = {}
        for pestana in PESTANAS:
            groups = []
            for libro in enriched:
                if libro["familia"] != familia:
                    continue
                spec = (libro.get("pestanas") or {}).get(pestana["id"]) or {}
                if spec.get("columns"):
                    groups.append(spec["columns"])
            stg = pestana["stg_sede"] if familia == "sede" else pestana["stg_od"]
            pestanas_out[pestana["id"]] = {
                "worksheet": pestana["worksheet"],
                "stg_table": stg,
                "pipeline": pestana["pipeline"],
                "columns": union_columns(groups),
            }
        catalog[familia] = {
            "libros": [libro for libro in enriched if libro["familia"] == familia],
            "pestanas": pestanas_out,
        }

    out = ROOT / "docs" / "inputs" / "fuentes_sheets.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"escrito {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
