"""SALIDA: DataFrame(s) -> Excel en output/."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

_SHEET_MAX = 31


def escribir_excel(df: pd.DataFrame, root: Path, *, nombre: str = "resultado.xlsx") -> Path:
    out_dir = root / "output"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / nombre
    df.to_excel(path, index=False, engine="openpyxl")
    print(f"Excel: {len(df)} filas x {len(df.columns)} columnas -> {path.relative_to(root)}")
    return path


def _sheet_name(name: str) -> str:
    clean = "".join(ch if ch.isalnum() or ch in " _-" else "_" for ch in str(name)).strip()
    return (clean or "HOJA")[:_SHEET_MAX]


def escribir_libro(
    hojas: dict[str, pd.DataFrame],
    root: Path,
    *,
    nombre: str = "fase1.xlsx",
) -> Path:
    """Escribe un xlsx con una hoja por DataFrame. Nombres de hoja <= 31 chars."""
    if not hojas:
        raise ValueError("escribir_libro: no hay hojas")
    out_dir = root / "output"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / nombre
    usados: set[str] = set()
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for raw, df in hojas.items():
            sheet = _sheet_name(raw)
            base = sheet
            n = 1
            while sheet in usados:
                suf = f"_{n}"
                sheet = (base[: _SHEET_MAX - len(suf)] + suf)
                n += 1
            usados.add(sheet)
            df.to_excel(writer, sheet_name=sheet, index=False)
            print(f"Excel[{sheet}]: {len(df)} x {len(df.columns)}")
    print(f"Excel: {len(hojas)} hojas -> {path.relative_to(root)}")
    return path
