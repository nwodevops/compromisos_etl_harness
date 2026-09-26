import re
import unicodedata

_VACIO = {"", "FALSE", "False", "false", "None", "nan"}
_META = ("FAMILIA", "COD_FUENTE")


def _norm(nombre):
    texto = re.sub(r"\s+", " ", str(nombre or "").replace("\n", " ")).strip()
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(ch for ch in texto if unicodedata.category(ch) != "Mn")
    return texto.casefold()


def _claves(df):
    return {_norm(col): col for col in df.columns if col not in _META}


def _reporte(titulo, sede, od):
    claves_sede = _claves(sede)
    claves_od = _claves(od)
    comunes = sorted(set(claves_sede) & set(claves_od))
    solo_sede = sorted(set(claves_sede) - set(claves_od))
    solo_od = sorted(set(claves_od) - set(claves_sede))
    print(f"APILADOS {titulo}: " + ", ".join(claves_sede[k] for k in comunes))
    print(f"SOLO_SEDE {titulo}: " + ", ".join(claves_sede[k] for k in solo_sede))
    print(f"SOLO_OD {titulo}: " + ", ".join(claves_od[k] for k in solo_od))


def _apilar(sede, od):
    sede = sede.copy()
    od = od.copy()
    sede["FAMILIA"] = "sede"
    od["FAMILIA"] = "od"
    claves_sede = _claves(sede)
    rename = {}
    for clave, col in _claves(od).items():
        if clave in claves_sede and claves_sede[clave] != col:
            rename[col] = claves_sede[clave]
    if rename:
        od = od.rename(columns=rename)
    out = pd.concat([sede, od], ignore_index=True, sort=False)
    datos = [col for col in out.columns if col not in _META]
    if datos:
        texto = out[datos].apply(lambda serie: serie.map(_celda))
        out = out.loc[~texto.isin(list(_VACIO)).all(axis=1)].copy()
    frente = [col for col in _META if col in out.columns]
    resto = [col for col in out.columns if col not in frente]
    out = out[frente + resto]
    return out.sort_values(["FAMILIA", "COD_FUENTE"], kind="mergesort", na_position="last")


_BOOL = {"HUMANOS", "FLORA", "FAUNA", "AGUA", "AIRE", "SUELO"}
_TOKEN = {
    "no aplica": "NO APLICA",
    "si": "SI",
    "no": "NO",
    "true": "TRUE",
    "false": "FALSE",
}


def _celda(valor):
    if valor is None:
        return ""
    try:
        if pd.isna(valor):
            return ""
    except TypeError:
        pass
    return str(valor).strip()


def _canon(columna, valor):
    """Unifica la misma celda: espacios, 'nan' vacío, y tokens de una sola grafía."""
    texto = _celda(valor)
    if texto.casefold() in {"nan", "none", "null"}:
        return ""
    texto = re.sub(r"\s+", " ", texto).strip()
    if not texto:
        return ""
    clave = _norm(texto)
    if columna in _BOOL:
        if clave in {"0", "false"}:
            return "FALSE"
        if clave in {"1", "true"}:
            return "TRUE"
        return texto
    return _TOKEN.get(clave, texto)


def _normalizar(df):
    out = df.copy()
    for col in out.columns:
        if col in _META:
            continue
        out[col] = out[col].map(lambda valor, c=col: _canon(c, valor))
    datos = [col for col in out.columns if col not in _META]
    if datos:
        out = out.loc[~out[datos].isin(list(_VACIO)).all(axis=1)].copy()
    return out


def _conteo(nombre, df):
    if df.empty:
        return pd.DataFrame(columns=["TABLA", "FAMILIA", "COD_FUENTE", "FILAS"])
    grupo = (
        df.groupby(["FAMILIA", "COD_FUENTE"], dropna=False)
        .size()
        .reset_index(name="FILAS")
    )
    grupo.insert(0, "TABLA", nombre)
    return grupo


_reporte("Reuniones", SEDE_REUNIONES, OD_REUNIONES)
_reporte("Base Acuerdos", SEDE_ACUERDOS, OD_ACUERDOS)
_reporte("Datos adicionales", SEDE_DATOS, OD_DATOS)

DF_REUNIONES = _normalizar(_apilar(SEDE_REUNIONES, OD_REUNIONES))
DF_BASE_ACUERDOS = _normalizar(_apilar(SEDE_ACUERDOS, OD_ACUERDOS))
DF_DATOS_ADICIONALES = _normalizar(_apilar(SEDE_DATOS, OD_DATOS))

RESULTADO = pd.concat(
    [
        _conteo("Reuniones", DF_REUNIONES),
        _conteo("Base Acuerdos", DF_BASE_ACUERDOS),
        _conteo("Datos adicionales", DF_DATOS_ADICIONALES),
    ],
    ignore_index=True,
)
