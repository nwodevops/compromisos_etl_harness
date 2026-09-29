"""TX_OFICINA y PK_OFICINA a partir de FAMILIA + COD_FUENTE.

Lee docs/inputs/oficinas.yaml y T_SEP_OFICINA del MySQL de entrada
(docs/credenciales/local.txt, bloque INPUT MySQL). No usa el DW local.
Un texto sin cruce deja PK_OFICINA vacío y sigue.
"""

from __future__ import annotations

import re
import sys
import unicodedata
from pathlib import Path

import pandas as pd
import yaml

HERE = Path(__file__).resolve().parent
PY = HERE.parent
if str(PY) not in sys.path:
    sys.path.insert(0, str(PY))

from config import project_root  # noqa: E402

HOJAS = ("DF_REUNIONES", "DF_BASE_ACUERDOS", "DF_DATOS_ADICIONALES")
COR_RE = re.compile(r"^cor\d+$")


def _norm(texto) -> str:
    text = re.sub(r"\s+", " ", str(texto or "").replace("\n", " ")).strip()
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    return text.casefold()


def _credencial_input(root: Path) -> dict[str, str]:
    path = root / "docs" / "credenciales" / "local.txt"
    if not path.is_file():
        raise FileNotFoundError(f"No se encuentra {path}")
    campos: dict[str, str] = {}
    dentro = False
    for line in path.read_text(encoding="utf-8").splitlines():
        if "INPUT" in line and "MySQL" in line:
            dentro = True
            continue
        if not dentro:
            continue
        if not line.strip():
            if campos:
                break
            continue
        if line.startswith("#"):
            break
        if ":" not in line:
            continue
        clave, valor = line.split(":", 1)
        campos[clave.strip().casefold()] = valor.strip()
    faltan = [k for k in ("host", "port", "database", "user", "password") if not campos.get(k)]
    if faltan:
        raise ValueError(f"INPUT MySQL en {path.name} sin {', '.join(faltan)}")
    return campos


def _catalogo(root: Path) -> list[dict]:
    cv = _credencial_input(root)
    import mysql.connector

    conn = mysql.connector.connect(
        host=cv["host"],
        port=int(cv["port"]),
        user=cv["user"],
        password=cv["password"],
        database=cv["database"],
        charset="utf8mb4",
    )
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(
            """
            SELECT PK_OFICINA, TX_DESCRIPCION, TX_ABREVIATURA, TX_ESTADO
            FROM T_SEP_OFICINA
            """
        )
        return list(cur.fetchall())
    finally:
        conn.close()


def _poner(indice: dict[str, str], texto, pk: str, origen: str) -> None:
    clave = _norm(texto)
    if not clave:
        return
    previo = indice.get(clave)
    if previo and previo != pk:
        raise ValueError(f"{origen} {texto!r} apunta a {previo} y a {pk}")
    indice[clave] = pk


def _poner_catalogo(indice: dict[str, str], ambiguos: set[str], texto, pk: str) -> None:
    clave = _norm(texto)
    if not clave or clave in ambiguos:
        return
    previo = indice.get(clave)
    if previo and previo != pk:
        ambiguos.add(clave)
        indice.pop(clave, None)
        return
    indice[clave] = pk


def _indices(root: Path) -> dict:
    path = root / "docs" / "inputs" / "oficinas.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    fuentes: dict[tuple[str, str], str] = {}
    for item in data.get("fuentes") or []:
        familia = _norm(item.get("familia"))
        cod = _norm(item.get("cod"))
        tx = str(item.get("tx_oficina") or "").strip()
        if not familia or not cod or not tx:
            raise ValueError(f"fuente incompleta: {item}")
        clave = (familia, cod)
        if clave in fuentes and fuentes[clave] != tx:
            raise ValueError(f"fuente duplicada {clave}")
        fuentes[clave] = tx

    sigla: dict[str, str] = {}
    for pk, texto in (data.get("siglas") or {}).items():
        _poner(sigla, texto, str(pk).strip(), "sigla")
    regla: dict[str, str] = {}
    for pk, nombres in (data.get("reglas") or {}).items():
        for nombre in nombres or []:
            _poner(regla, nombre, str(pk).strip(), "regla")

    pk_idx: dict[str, str] = {}
    desc: dict[str, str] = {}
    ambiguos: set[str] = set()
    for fila in _catalogo(root):
        if str(fila.get("TX_ESTADO") or "").strip() != "1":
            continue
        pk = str(fila.get("PK_OFICINA") or "").strip()
        if not pk:
            continue
        _poner(pk_idx, pk, pk, "PK_OFICINA")
        _poner_catalogo(desc, ambiguos, fila.get("TX_DESCRIPCION"), pk)
        abrev = str(fila.get("TX_ABREVIATURA") or "").strip()
        if abrev:
            _poner(sigla, abrev, pk, "TX_ABREVIATURA")

    for nombre, indice in (("sigla", sigla), ("regla", regla)):
        for clave, pk in indice.items():
            otro = desc.get(clave)
            if otro and otro != pk:
                raise ValueError(f"{nombre} {clave!r} es {pk} y TX_DESCRIPCION es {otro}")
    return {"fuentes": fuentes, "pk": pk_idx, "desc": desc, "sigla": sigla, "regla": regla}


def _pk(texto: str, idx: dict) -> str:
    clave = _norm(texto)
    if not clave:
        return ""
    if COR_RE.match(clave) and clave in idx["pk"]:
        return idx["pk"][clave]
    for nombre in ("desc", "sigla", "regla"):
        if clave in idx[nombre]:
            return idx[nombre][clave]
    return ""


def _aplicar_df(df: pd.DataFrame, idx: dict, titulo: str) -> pd.DataFrame:
    out = df.copy()
    for col in ("TX_OFICINA", "PK_OFICINA"):
        if col in out.columns:
            out = out.drop(columns=[col])
    if "FAMILIA" not in out.columns or "COD_FUENTE" not in out.columns:
        raise ValueError(f"{titulo} sin FAMILIA o COD_FUENTE")

    textos: list[str] = []
    pks: list[str] = []
    vistos: set[str] = set()
    for familia, cod in zip(out["FAMILIA"], out["COD_FUENTE"]):
        tx = idx["fuentes"].get((_norm(familia), _norm(cod)), "")
        pk = _pk(tx, idx)
        textos.append(tx)
        pks.append(pk)
        if pk:
            continue
        aviso = f"{_norm(familia)}|{_norm(cod)}|{tx}"
        if aviso in vistos:
            continue
        vistos.add(aviso)
        mostrado = tx or "(sin TX_OFICINA)"
        print(f"SIN_CRUCE {titulo}: {familia} {cod} -> {mostrado}")

    pos = list(out.columns).index("COD_FUENTE") + 1
    out.insert(pos, "TX_OFICINA", textos)
    out.insert(pos + 1, "PK_OFICINA", pks)
    return out


def aplicar(root: Path, hojas: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    idx = _indices(root)
    out = dict(hojas)
    for clave in HOJAS:
        if clave in out:
            out[clave] = _aplicar_df(out[clave], idx, clave)
    return out


if __name__ == "__main__":
    raise SystemExit("lo llama python/main.py")
