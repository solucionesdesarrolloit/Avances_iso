import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import os

# --- CONFIGURACIÓN DE CONEXIÓN ---
DB_USER = "postgres"
DB_PASSWORD = "1234"
DB_HOST = "localhost"
DB_PORT = "5432" 
DB_NAME = "avances_iso"

# --- CADENA DE CONEXIÓN PARA POSTGRESQL ---
engine = create_engine(f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

# ==========================
# CONFIGURACIÓN DE PÁGINA
# ==========================

st.set_page_config(page_title="Control de Captura", layout="wide")
st.title("📋 Control de Captura de Avances")

# ==========================
# FILTROS
# ==========================

# Años y meses
anios = [2025, 2026, 2027, 2028]
meses = [
    "Enero","Febrero","Marzo","Abril","Mayo","Junio",
    "Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"
]

# Obtener procesos desde combinaciones_base
with engine.connect() as conn:
    procesos_df = pd.read_sql("SELECT DISTINCT proceso FROM combinaciones_base", conn)

procesos = procesos_df["proceso"].tolist()

col1, col2, col3 = st.columns(3)

with col1:
    anio_sel = st.selectbox("Año", anios)

with col2:
    mes_sel = st.selectbox("Mes", meses)

with col3:
    proceso_sel = st.selectbox("Proceso (opcional)", ["Todos"] + procesos)

# ==========================
# CONSULTA PRINCIPAL
# ==========================

query = """
SELECT 
    cb.proceso,
    cb.indicador,
    cb.unidad,
    CASE 
        WHEN a.proceso IS NULL THEN '❌ No reportado'
        ELSE '✅ Reportado'
    END AS estatus
FROM combinaciones_base cb
LEFT JOIN avances a
    ON cb.proceso = a.proceso
    AND cb.indicador = a.indicador
    AND cb.unidad = a.unidad
    AND a.anio = :anio
    AND a.mes = :mes
"""

params = {"anio": anio_sel, "mes": mes_sel}

if proceso_sel != "Todos":
    query += " WHERE cb.proceso = :proceso"
    params["proceso"] = proceso_sel

with engine.connect() as conn:
    df_control = pd.read_sql(text(query), conn, params=params)

# ==========================
# MÉTRICAS RESUMEN
# ==========================

total = len(df_control)
reportados = len(df_control[df_control["estatus"].str.contains("Reportado")])
faltantes = total - reportados
cumplimiento = round((reportados / total) * 100, 2) if total > 0 else 0

st.divider()

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total esperados", total)
col2.metric("Reportados", reportados)
col3.metric("Faltantes", faltantes)
col4.metric("% Cumplimiento", f"{cumplimiento}%")

st.divider()

# ==========================
# TABLA COLOREADA
# ==========================

def color_estatus(val):
    if "No reportado" in val:
        return "background-color: #ffcccc"
    else:
        return "background-color: #ccffcc"

st.dataframe(
    df_control.style.applymap(color_estatus, subset=["estatus"]),
    use_container_width=True
)

# ==========================
# OPCIÓN: MOSTRAR SOLO FALTANTES
# ==========================

if st.checkbox("Mostrar solo faltantes"):
    df_faltantes = df_control[df_control["estatus"].str.contains("No reportado")]
    st.dataframe(
        df_faltantes,
        use_container_width=True
    )