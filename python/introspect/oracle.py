"""Introspección Oracle: ALL_TAB_COLUMNS. No extrae filas."""

from __future__ import annotations

from config import require_live_conn
from .h2_ddl import Column, map_h2_type, sanitize_ident


def _split_object(object_name: str) -> tuple[str, str]:
    parts = object_name.strip().split(".")
    if len(parts) != 2:
        raise ValueError(
            f"object Oracle debe ser OWNER.NOMBRE, recibido: {object_name!r}"
        )
    return parts[0].upper(), parts[1].upper()


def introspect(source: dict, variables: dict[str, str], root=None) -> list[Column]:
    try:
        import oracledb
    except ImportError as exc:
        raise SystemExit(
            "Falta oracledb. Instala: pip install -r python/requirements.txt"
        ) from exc

    try:
        oracledb.init_oracle_client()
    except Exception:
        pass

    connection = source.get("connection") or "oracle_sisud"
    object_name = source.get("object")
    if not object_name:
        raise ValueError(f"{source.get('stg_table')}: falta object (OWNER.NOMBRE)")

    owner, table = _split_object(object_name)
    cv = require_live_conn(connection, variables)
    port = int(cv["port"]) if str(cv["port"]).isdigit() else 1521

    conn = oracledb.connect(
        user=cv["username"],
        password=cv["password"],
        host=cv["host"],
        port=port,
        service_name=cv["database"],
    )
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT COLUMN_NAME, DATA_TYPE, DATA_SCALE
                FROM ALL_TAB_COLUMNS
                WHERE OWNER = :owner AND TABLE_NAME = :tname
                ORDER BY COLUMN_ID
                """,
                {"owner": owner, "tname": table},
            )
            rows = cur.fetchall()
    finally:
        conn.close()

    if not rows:
        raise ValueError(f"Oracle {owner}.{table}: 0 columnas (¿owner/nombre mal?)")

    used: set[str] = set()
    cols: list[Column] = []
    for name, data_type, scale in rows:
        sc = None if scale is None else int(scale)
        cols.append(
            Column(
                name=sanitize_ident(str(name), used),
                h2_type=map_h2_type(str(data_type), scale=sc),
            )
        )
    return cols
