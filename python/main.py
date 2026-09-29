#!/usr/bin/env python3
"""ENTRY POINT capa lógica post-staging (arquetipo mínimo).

  1. SETUP   : project-config.json
  2. ENTRADA : io/leer_h2.py -> DataFrames (LECTURAS)
  3. LOGICA  : único .py en logica/
  4. SALIDA  : logs + Excel (output/resultado.xlsx)

Contrato: python/CONTRATO.md
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from config import load_vars, project_root  # noqa: E402

SALIDA_DF = "RESULTADO"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"No se pudo cargar {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _es_salida(nombre: str) -> bool:
    if nombre == SALIDA_DF:
        return True
    return nombre.startswith(("INT_", "QA_", "PROF_", "DF_"))


def main() -> int:
    root = project_root()
    variables = load_vars(root)

    leer = _load("leer_h2", HERE / "io" / "leer_h2.py")
    datos = leer.leer_h2(root, variables)
    if not datos:
        raise SystemExit("leer_h2() no devolvió DataFrames; revisa LECTURAS")

    logica_dir = root / "logica"
    archivos = sorted(p for p in logica_dir.glob("*.py") if p.name != "__init__.py")
    if not archivos:
        raise SystemExit("No hay .py en logica/. Copia python/plantilla_logica.py")
    if len(archivos) > 1:
        raise SystemExit(f"Hay más de un .py en logica/: {[p.name for p in archivos]}")

    print(f"Logica: {archivos[0].name}")
    import pandas as pd

    if str(logica_dir) not in sys.path:
        sys.path.insert(0, str(logica_dir))

    ns: dict = {"__name__": "__logica__", "__file__": str(archivos[0]), "pd": pd}
    ns.update(datos)
    exec(compile(archivos[0].read_text(encoding="utf-8"), str(archivos[0]), "exec"), ns)

    salidas: dict[str, pd.DataFrame] = {}
    for nombre, val in ns.items():
        if _es_salida(nombre) and isinstance(val, pd.DataFrame):
            salidas[nombre] = val

    if SALIDA_DF not in salidas:
        raise SystemExit(f"La lógica no dejó '{SALIDA_DF}'. Ver python/CONTRATO.md")

    ofi = HERE / "io" / "oficinas.py"
    if ofi.is_file():
        resolver = _load("oficinas", ofi)
        salidas = resolver.aplicar(root, salidas)

    for nombre, df in salidas.items():
        print(f"Salida {nombre}: {len(df)} filas x {len(df.columns)} columnas")

    escribir = _load("escribir_excel", HERE / "io" / "escribir_excel.py")
    nombres = {
        "DF_REUNIONES": "Reuniones",
        "DF_BASE_ACUERDOS": "Base Acuerdos",
        "DF_DATOS_ADICIONALES": "Datos adicionales",
        SALIDA_DF: "Conteos",
    }
    hojas = {}
    for clave in ("DF_REUNIONES", "DF_BASE_ACUERDOS", "DF_DATOS_ADICIONALES", SALIDA_DF):
        if clave in salidas:
            hojas[nombres[clave]] = salidas[clave]
    if len(hojas) > 1:
        escribir.escribir_libro(hojas, root, nombre="resultado.xlsx")
    else:
        escribir.escribir_excel(salidas[SALIDA_DF], root)

    acu = HERE / "io" / "cargar_acu.py"
    if acu.is_file():
        cargar = _load("cargar_acu", acu)
        cargar.publicar(root, hojas)
        print("Listo (H2 -> logica -> Excel + DW_ACU_*).")
    else:
        print("Listo (H2 -> logica -> Excel).")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (FileNotFoundError, ValueError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
