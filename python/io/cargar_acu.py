"""Publica las 3 tablas de acuerdos en Oracle DW y en MySQL DW.

Nombres: DW_ACU_REUNIONES, DW_ACU_BASE_ACUERDOS, DW_ACU_DATOS.
Si las tres vienen vacías, no toca el destino (el smoke de init.sh no borra la carga).
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from config import load_vars, project_root, require_live_conn

TABLAS = (
    ("Reuniones", "DW_ACU_REUNIONES"),
    ("Base Acuerdos", "DW_ACU_BASE_ACUERDOS"),
    ("Datos adicionales", "DW_ACU_DATOS"),
)

TABLA_COMENTARIO = {
    "DW_ACU_REUNIONES": (
        "Reuniones de sede central y oficinas desconcentradas. "
        "Una fila por reunión y libro de origen."
    ),
    "DW_ACU_BASE_ACUERDOS": (
        "Acuerdos de cada reunión, sede y OD apilados por nombre de columna. "
        "Las tres columnas de estado miden cosas distintas y no se fusionan."
    ),
    "DW_ACU_DATOS": (
        "Datos adicionales del acuerdo: ubicación, componentes afectados "
        "y escalas de cantidad, extensión y peligrosidad."
    ),
}

COLUMNA_COMENTARIO = {
    "FAMILIA": "Grupo de origen: sede o od.",
    "COD_FUENTE": "Libro de origen: CMIN, AMAZONAS, LA LIBERTAD, etc.",
    "COD_REUNION": "Código de la reunión en el libro de origen.",
    "SOL_REUNION": "Quien solicita la reunión.",
    "FEC_REUNION": "Fecha de la reunión.",
    "HORAI_REUNION": "Hora de inicio de la reunión.",
    "HORAF_REUNION": "Hora de fin de la reunión.",
    "LUGAR_REUNION": "Lugar de la reunión.",
    "AGENDA": "Agenda de la reunión.",
    "NRO_EXPEDIENTE": "Número de expediente.",
    "COD_ACCION": "Código de la acción de supervisión.",
    "ADM": "Administrado.",
    "UF": "Unidad de fiscalización.",
    "EXIST_ACUERDOS": "Indica si la reunión tiene acuerdos: SI o NO.",
    "CANT_ACUERDOS": "Cantidad de acuerdos. Viene de sede; en OD queda vacío.",
    "TIPO_DOC": "Tipo de documento de la reunión.",
    "COMENTARIOS": "Comentarios libres de la fila.",
    "AUX": "Columna auxiliar del libro OD. En sede queda vacía.",
    "NRO_ACUERDO": "Número del acuerdo.",
    "COR_ACUERDO": "Correlativo del acuerdo dentro de la reunión.",
    "DESCRIPCION_ACUERDO": "Descripción del acuerdo.",
    "PLAZO_CUMPLIMIENTO": "Plazo pactado para cumplir el acuerdo.",
    "FECHA_PROYECTADA": "Fecha proyectada de cumplimiento.",
    "ESTADO_CUMPLIMIENTO": (
        "Situación del plazo: VENCIDO o EN PLAZO. "
        "No indica si el acuerdo se cumplió."
    ),
    "ESTADO_ACUERDO": (
        "Situación del acuerdo: EN EJECUCIÓN, CUMPLIDO, INCUMPLIDO "
        "o VARIADA (DEJADA SIN EFECTO)."
    ),
    "FECHA_CUMPLIMIENTO": "Fecha en que se cumplió el acuerdo.",
    "ESTADO_VERIFICACION": (
        "Avance de la verificación: EN ELABORACIÓN, VERIFICADO "
        "o TERMINADO (CONCLUÍDO). Vacío si aún no hay verificación."
    ),
    "MEDIO_VERIF": "Medio usado para verificar el acuerdo.",
    "TIPO_DOC_VERIFICACION": "Tipo de documento de la verificación.",
    "DOC_VERIFICACION": "Documento de la verificación.",
    "AMERITA_MEDIDA_ADMIN": "Indica si el acuerdo amerita medida administrativa.",
    "NRO_RESOL": "Número de resolución.",
    "FECHA_EMISION_APROB": "Fecha de emisión o aprobación.",
    "SUSTENTO_AC": "Sustento del acuerdo. NO APLICA queda en una sola grafía.",
    "FECHA_DETEC_INICIO": "Inicio del periodo de detección.",
    "FECHA_DETEC_FIN": "Fin del periodo de detección.",
    "REGION": "Región del hecho.",
    "PROVINCIA": "Provincia del hecho.",
    "DISTRITO": "Distrito del hecho.",
    "ANALIS_LAB_AC": "Indica si hay análisis de laboratorio: SI o NO.",
    "DANO_RIESGO": "Clasificación del hecho: DAÑO, RIESGO o NO APLICA.",
    "HUMANOS": "Componente humanos afectado: TRUE o FALSE. 1 y 0 se normalizan.",
    "FLORA": "Componente flora afectada: TRUE o FALSE. 1 y 0 se normalizan.",
    "FAUNA": "Componente fauna afectada: TRUE o FALSE. 1 y 0 se normalizan.",
    "AGUA": "Componente agua afectada: TRUE o FALSE. 1 y 0 se normalizan.",
    "AIRE": "Componente aire afectado: TRUE o FALSE. 1 y 0 se normalizan.",
    "SUELO": "Componente suelo afectado: TRUE o FALSE. 1 y 0 se normalizan.",
    "CANTIDAD_N": "Escala de cantidad del medio natural. Distinta de CANTIDAD_H.",
    "EXTENSION_N": "Escala de extensión del medio natural. Distinta de EXTENSION_H.",
    "PELIGROSIDAD_N": "Escala de peligrosidad del medio natural. Distinta de PELIGROSIDAD_H.",
    "MEDIO_POTENCIALMENTE_AFECTADO_N": "Medio natural potencialmente afectado.",
    "CANTIDAD_H": "Escala de cantidad para la salud humana. Distinta de CANTIDAD_N.",
    "EXTENSION_H": "Escala de extensión para la salud humana. Distinta de EXTENSION_N.",
    "PELIGROSIDAD_H": "Escala de peligrosidad para la salud humana. Distinta de PELIGROSIDAD_N.",
    "PERSONAS_POTENCIALMENTE_EXPUESTAS_H": "Escala de personas potencialmente expuestas.",
    "PROBABILIDAD": "Probabilidad del riesgo. NO APLICA queda en una sola grafía.",
}


def _sql_texto(texto: str) -> str:
    return "'" + texto.replace("'", "''") + "'"


def _comentario(col: str) -> str:
    return COLUMNA_COMENTARIO.get(col, f"Columna {col} de la hoja de origen, con el texto normalizado.")


def _vacio(valor) -> bool:
    if valor is None:
        return True
    try:
        if pd.isna(valor):
            return True
    except TypeError:
        pass
    return str(valor).strip() == ""


def _celdas(df: pd.DataFrame) -> list[tuple]:
    frame = df.where(pd.notna(df), None)
    filas = []
    for row in frame.itertuples(index=False, name=None):
        filas.append(tuple(None if _vacio(v) else str(v) for v in row))
    return filas


def _mysql(root: Path, tablas: list[tuple[str, pd.DataFrame]]) -> None:
    variables = load_vars(root)
    cv = require_live_conn("mysql_dw", variables)
    import mysql.connector

    port = int(cv["port"]) if str(cv["port"]).isdigit() else 3306
    conn = mysql.connector.connect(
        host=cv["host"],
        port=port,
        user=cv["username"],
        password=cv["password"],
        database=cv["database"],
        charset="utf8mb4",
        autocommit=False,
    )
    try:
        cur = conn.cursor()
        for nombre, df in tablas:
            cols = [str(c) for c in df.columns]
            defs = []
            for col in cols:
                if col == "FAMILIA":
                    tipo = "VARCHAR(16)"
                elif col == "COD_FUENTE":
                    tipo = "VARCHAR(80)"
                else:
                    tipo = "TEXT"
                defs.append(f"`{col}` {tipo} COMMENT {_sql_texto(_comentario(col))}")
            cur.execute(f"DROP TABLE IF EXISTS `{nombre}`")
            cur.execute(
                f"CREATE TABLE `{nombre}` ({', '.join(defs)}) ENGINE=InnoDB "
                f"DEFAULT CHARSET=utf8mb4 COMMENT={_sql_texto(TABLA_COMENTARIO[nombre])}"
            )
            if df.empty:
                print(f"MySQL {nombre}: 0 filas")
                continue
            marcas = ", ".join(["%s"] * len(cols))
            lista = ", ".join(f"`{c}`" for c in cols)
            cur.executemany(
                f"INSERT INTO `{nombre}` ({lista}) VALUES ({marcas})",
                _celdas(df),
            )
            print(f"MySQL {nombre}: {len(df)} filas")
        conn.commit()
        print(f"MySQL DW: {cv['username']}@{cv['host']}:{cv['port']}/{cv['database']}")
    finally:
        conn.close()


def _oracle(root: Path, tablas: list[tuple[str, pd.DataFrame]]) -> None:
    variables = load_vars(root)
    cv = require_live_conn("oracle_dw", variables)
    import oracledb

    dsn = f"{cv['host']}:{cv['port']}/{cv['database']}"
    conn = oracledb.connect(user=cv["username"], password=cv["password"], dsn=dsn)
    try:
        cur = conn.cursor()
        for nombre, df in tablas:
            cur.execute(
                """
                BEGIN
                  EXECUTE IMMEDIATE 'DROP TABLE ' || :t;
                EXCEPTION
                  WHEN OTHERS THEN
                    IF SQLCODE != -942 THEN RAISE; END IF;
                END;
                """,
                {"t": nombre},
            )
            cols = [str(c) for c in df.columns]
            defs = []
            for col in cols:
                if col == "FAMILIA":
                    tipo = "VARCHAR2(16)"
                elif col == "COD_FUENTE":
                    tipo = "VARCHAR2(80)"
                else:
                    tipo = "CLOB"
                defs.append(f"{col} {tipo}")
            cur.execute(f"CREATE TABLE {nombre} ({', '.join(defs)})")
            cur.execute(
                f"COMMENT ON TABLE {nombre} IS {_sql_texto(TABLA_COMENTARIO[nombre])}"
            )
            for col in cols:
                cur.execute(
                    f"COMMENT ON COLUMN {nombre}.{col} IS {_sql_texto(_comentario(col))}"
                )
            if df.empty:
                print(f"Oracle {nombre}: 0 filas")
                continue
            marcas = ", ".join(f":{i + 1}" for i in range(len(cols)))
            lista = ", ".join(cols)
            cur.executemany(
                f"INSERT INTO {nombre} ({lista}) VALUES ({marcas})",
                _celdas(df),
            )
            print(f"Oracle {nombre}: {len(df)} filas")
        conn.commit()
        print(f"Oracle DW: {cv['username']}@{dsn}")
    finally:
        conn.close()


def publicar(root: Path, hojas: dict[str, pd.DataFrame]) -> None:
    tablas = []
    for hoja, nombre in TABLAS:
        df = hojas.get(hoja)
        if df is None:
            raise ValueError(f"falta la hoja {hoja} para {nombre}")
        tablas.append((nombre, df))
    if all(df.empty for _, df in tablas):
        print("AVISO: DW_ACU_* sin filas; no se reemplazan Oracle ni MySQL")
        return
    _mysql(root, tablas)
    _oracle(root, tablas)


def publicar_excel(root: Path | None = None) -> None:
    root = root or project_root()
    path = root / "output" / "resultado.xlsx"
    hojas = {
        hoja: pd.read_excel(path, sheet_name=hoja)
        for hoja, _nombre in TABLAS
    }
    publicar(root, hojas)


if __name__ == "__main__":
    publicar_excel()
