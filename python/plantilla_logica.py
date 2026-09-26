# =============================================================================
# plantilla_logica.py  --  PLANTILLA DE LOGICA (copia a logica/ en la raiz, no a python/)
#
# PARA UN ETL NUEVO:
#   1. Copiar este archivo a  logica/<tu_logica>.py  (un solo .py)
#   2. Escribir tu transformacion usando los DataFrames de entrada
#      (nombres = claves de LECTURAS en python/io/leer_h2.py).
#   3. Dejar al final un DataFrame con el nombre SALIDA_DF (default "RESULTADO").
#
# AISLAMIENTO (reglas):
#   - NO abrir conexiones ni cargar drivers: el I/O lo hace main.py / io/.
#   - NO usar rutas de archivo: el DataFrame ya viene en memoria.
#   - Solo pandas / stdlib sobre los DataFrames inyectados.
# =============================================================================

# Ejemplo trivial sobre la lectura DEMO (DEMO_TABLA_EJEMPLO):
# DEMO -> RESULTADO
RESULTADO = DEMO[["ID", "TXNOMBRE", "FEALTA"]].copy()
RESULTADO["FEALTA"] = pd.to_datetime(RESULTADO["FEALTA"]).dt.date

# <--- AQUI VA TU LOGICA (deja el df con el nombre SALIDA_DF) --->
