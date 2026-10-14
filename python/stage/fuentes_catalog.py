"""Catálogo de Google Sheets (sede central + OD).

No descarga filas. Lee docs/inputs/fuentes_sheets.json y arma los
nombres de columna STG con la misma limpieza que la lógica:
recortar, colapsar espacios, minúsculas, sin tildes.
"""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

DEFAULT_REL = Path("docs/inputs/fuentes_sheets.json")
CODE_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")

PESTANAS = (
    {
        "id": "reuniones",
        "worksheet": "Reuniones",
        "stg_sede": "STG_SEDE_REUNIONES",
        "stg_od": "STG_OD_REUNIONES",
        "pipeline": "pl_stage_reuniones.hpl",
    },
    {
        "id": "acuerdos",
        "worksheet": "Base Acuerdos",
        "stg_sede": "STG_SEDE_ACUERDOS",
        "stg_od": "STG_OD_ACUERDOS",
        "pipeline": "pl_stage_acuerdos.hpl",
    },
    {
        "id": "datos",
        "worksheet": "Datos adicionales Acuerdos",
        "stg_sede": "STG_SEDE_DATOS",
        "stg_od": "STG_OD_DATOS",
        "pipeline": "pl_stage_datos.hpl",
    },
)


def catalog_path(root: Path, rel: str | Path | None = None) -> Path:
    return (root / (rel or DEFAULT_REL)).resolve()


def load_catalog(root: Path, rel: str | Path | None = None) -> dict:
    path = catalog_path(root, rel)
    if not path.is_file():
        raise FileNotFoundError(f"Catálogo no encontrado: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: raíz debe ser un objeto JSON")
    return data


def norm_header(value: str) -> str:
    text = re.sub(r"\s+", " ", str(value or "").replace("\n", " ")).strip()
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    return text.casefold()


def stg_columns(catalog: dict, familia: str | None = None, pestana: str | None = None) -> list[str]:
    """Nombres crudos (fila de códigos) más COD_FUENTE. create_stg sanitiza."""
    if not familia or not pestana:
        raise ValueError("sheets catalog: faltan familia y pestana")
    fam = catalog.get(familia)
    if not isinstance(fam, dict):
        raise ValueError(f"catálogo sin familia {familia!r}")
    spec = (fam.get("pestanas") or {}).get(pestana)
    if not isinstance(spec, dict):
        raise ValueError(f"catálogo {familia}.{pestana} sin definición")
    cols = [str(c) for c in (spec.get("columns") or []) if str(c).strip()]
    if not cols:
        raise ValueError(f"catálogo {familia}.{pestana} sin columns")
    if "COD_FUENTE" not in cols:
        cols = ["COD_FUENTE"] + cols
    return cols


def code_header(rows: list[list]) -> tuple[int, list[str]] | None:
    """Fila de códigos (COD_REUNION, …). Devuelve (fila 1-based, columnas)."""
    found: tuple[int, list[str]] | None = None
    for i, row in enumerate(rows):
        cells = [str(c).strip() for c in row]
        while cells and not cells[-1]:
            cells.pop()
        nonempty = [c for c in cells if c]
        if len(nonempty) < 8:
            continue
        ncode = sum(1 for c in nonempty if CODE_RE.match(c))
        if ncode >= max(8, int(0.8 * len(nonempty))):
            if any(not c for c in cells):
                raise ValueError(f"fila de códigos {i + 1} con hueco interno: {cells}")
            found = (i + 1, cells)
    return found


def union_columns(groups: list[list[str]]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for cols in groups:
        for col in cols:
            key = norm_header(col)
            if not key or key in seen:
                continue
            seen.add(key)
            out.append(col)
    return out
