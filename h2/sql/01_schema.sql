-- ============================================================
-- Schema H2 in-memory (mem:csep) para el proyecto.
-- Se ejecuta SIEMPRE despues del start del server H2
-- (h2/scripts/reset_and_create.sh → sql/00_reset.sql → sql/01_schema.sql).
--
-- REGLAS DEL ARQUETIPO:
--  * H2 es in-memory: cada corrida del workflow empieza con
--    stop + start + DROP ALL + este DDL. Todo se regenera.
--  * VARCHAR sin longitud = maximo en H2 (evita Value too long).
--  * Agrega aqui las tablas/vistas/indices propios del proyecto.
-- ============================================================

CREATE SCHEMA IF NOT EXISTS PUBLIC;

-- Tabla de ejemplo usada por workflows/wf_main.hwf + pipelines/pl_demo.hpl
CREATE TABLE IF NOT EXISTS DEMO_TABLA_EJEMPLO (
    ID       INT PRIMARY KEY,
    TXNOMBRE VARCHAR,
    FEALTA   TIMESTAMP
);

INSERT INTO DEMO_TABLA_EJEMPLO (ID, TXNOMBRE, FEALTA) VALUES
    (1, 'fila demo 1', CURRENT_TIMESTAMP),
    (2, 'fila demo 2', CURRENT_TIMESTAMP);

-- ============================================================
-- >>> DDL PROPIO DEL PROYECTO (reemplazar/ampliar lo de arriba) <<<
-- Ejemplo:
--   CREATE TABLE PUBLIC.DW_M_TABLA (...);
--   CREATE INDEX ... ;
-- ============================================================
