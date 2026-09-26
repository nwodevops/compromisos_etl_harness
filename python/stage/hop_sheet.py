"""Escribe un pipeline Hop GoogleSheetsInput → TableOutput para un libro."""

from __future__ import annotations

from pathlib import Path
from xml.sax.saxutils import escape


def _field_xml(name: str) -> str:
    return f"""      <field>
        <name>{escape(name)}</name>
        <position>0</position>
        <length>-1</length>
        <type>2</type>
        <INPUT_IGNORE>N</INPUT_IGNORE>
        <format/>
        <trim_type>0</trim_type>
        <precision>-1</precision>
        <currency/>
        <decimal/>
        <group/>
        <INPUT_FIELDS>N</INPUT_FIELDS>
      </field>"""


def _map_xml(name: str) -> str:
    safe = escape(name)
    return f"""      <field>
        <stream_name>{safe}</stream_name>
        <column_name>{safe}</column_name>
      </field>"""


def write_pipeline(
    path: Path,
    *,
    name: str,
    spreadsheet_key: str,
    worksheet: str,
    data_row: int,
    columns: list[str],
    table: str,
    credential: Path,
) -> None:
    """columns = nombres ya sanitizados, en el orden de la hoja.

    data_row es la fila de códigos. Hop la descarta y carga desde la siguiente.
    """
    if data_row < 1:
        raise ValueError(f"data_row inválida: {data_row}")
    rango = f"'{worksheet}'!A{data_row}:AZ"
    fields = "\n".join(_field_xml(col) for col in columns)
    maps = "\n".join(_map_xml(col) for col in columns)
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<pipeline>
  <info>
    <name>{escape(name)}</name>
    <name_sync_with_filename>N</name_sync_with_filename>
    <description>GoogleSheetsInput por orden de la fila de códigos. COD_FUENTE lo pone stage_sheets.py.</description>
    <extended_description/>
    <pipeline_version/>
    <pipeline_type>Normal</pipeline_type>
    <parameters>
    </parameters>
    <capture_transform_performance>N</capture_transform_performance>
    <transform_performance_capturing_delay>1000</transform_performance_capturing_delay>
    <transform_performance_capturing_size_limit>100</transform_performance_capturing_size_limit>
    <created_user>-</created_user>
    <created_date>2026/09/26 12:00:00.000</created_date>
    <modified_user>-</modified_user>
    <modified_date>2026/09/26 12:00:00.000</modified_date>
    <key_for_session_key>H4sIAAAAAAAAAAMAAAAAAAAAAAA=</key_for_session_key>
    <is_key_private>N</is_key_private>
  </info>
  <notepads>
  </notepads>
  <order>
    <hop>
      <from>Google Sheets</from>
      <to>H2 {escape(table)}</to>
      <enabled>Y</enabled>
    </hop>
  </order>
  <transform>
    <type>GoogleSheetsInput</type>
    <name>Google Sheets</name>
    <description/>
    <jsonCredentialPath>{escape(str(credential))}</jsonCredentialPath>
    <spreadsheetKey>{escape(spreadsheet_key)}</spreadsheetKey>
    <worksheetId>{escape(rango)}</worksheetId>
    <sampleFields>100</sampleFields>
    <timeout>60</timeout>
    <impersonation/>
    <appName>ApacheHop</appName>
    <fields>
{fields}
    </fields>
    <proxyHost/>
    <proxyPort/>
    <distribute>Y</distribute>
    <copies>1</copies>
    <partitioning>
      <method>none</method>
      <schema_name/>
    </partitioning>
    <attributes/>
    <GUI>
      <xloc>128</xloc>
      <yloc>160</yloc>
    </GUI>
  </transform>
  <transform>
    <name>H2 {escape(table)}</name>
    <type>TableOutput</type>
    <description>Append. COD_FUENTE queda null.</description>
    <distribute>Y</distribute>
    <custom_distribution/>
    <copies>1</copies>
    <partitioning>
      <method>none</method>
      <schema_name/>
    </partitioning>
    <connection>h2</connection>
    <schema>PUBLIC</schema>
    <table>{escape(table)}</table>
    <commit>1000</commit>
    <truncate>N</truncate>
    <only_when_have_rows>N</only_when_have_rows>
    <ignore_errors>N</ignore_errors>
    <use_batch>Y</use_batch>
    <partitioning_enabled>N</partitioning_enabled>
    <partitioning_field/>
    <partitioning_daily>N</partitioning_daily>
    <partitioning_monthly>N</partitioning_monthly>
    <tablename_in_field>N</tablename_in_field>
    <tablename_field/>
    <tablename_in_table>N</tablename_in_table>
    <return_keys>N</return_keys>
    <return_field/>
    <specify_fields>Y</specify_fields>
    <auto_update_table_structure>N</auto_update_table_structure>
    <always_drop_and_recreate>N</always_drop_and_recreate>
    <add_columns>N</add_columns>
    <drop_columns>N</drop_columns>
    <change_column_types>N</change_column_types>
    <fields>
{maps}
    </fields>
    <attributes/>
    <GUI>
      <xloc>400</xloc>
      <yloc>160</yloc>
    </GUI>
  </transform>
  <transform_error_handling>
  </transform_error_handling>
  <attributes/>
</pipeline>
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(xml, encoding="utf-8")
