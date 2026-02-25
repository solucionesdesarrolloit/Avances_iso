import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text

# --- CONFIGURACIÓN DE CONEXIÓN ---
DB_USER = "root"
DB_PASSWORD = "Pass1234"
DB_HOST = "127.0.0.1"
DB_PORT = "3306" 
DB_NAME = "avances_ISO"

# --- CADENA DE CONEXIÓN PARA MYSQL ---
engine = create_engine(f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")


# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Control de Avances", layout="wide")
st.header("📝 Registrar avances")

# --- OPCIONES DE AÑO Y MES ---
anios = [2025, 2026, 2027, 2028, 2029]
meses = [
    "Enero","Febrero","Marzo","Abril","Mayo","Junio",
    "Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"
]

# --- LEER COMBINACIONES BASE ---
with engine.connect() as conn:
    combinaciones_df = pd.read_sql("SELECT * FROM combinaciones_base", conn)

# Filtrar opciones únicas de procesos
procesos = combinaciones_df["proceso"].unique().tolist()
proceso = st.selectbox("Proceso", procesos)

# Filtrar indicadores según proceso
indicadores = combinaciones_df[combinaciones_df["proceso"] == proceso]["indicador"].unique().tolist()
indicador = st.selectbox("Indicador", indicadores)

# Filtrar unidades, frecuencias y meta según proceso+indicador
subset = combinaciones_df[
    (combinaciones_df["proceso"] == proceso) &
    (combinaciones_df["indicador"] == indicador)
]

unidades = subset["unidad"].unique().tolist()
frecuencias = subset["frecuencia"].unique().tolist()
metas = subset["meta"].unique().tolist()

# --- FORMULARIO ---
with st.form("form_avance"):
    col1, col2 = st.columns(2)

    with col1:
        unidad = st.selectbox("Unidad de negocio", unidades)
        anio = st.selectbox("Año", anios)
        mes = st.selectbox("Mes", meses)

    with col2:
        frecuencia = st.selectbox("Frecuencia", frecuencias)
        meta = st.selectbox("Meta", metas)
        avance = st.number_input("Avance (%)", min_value=0.0, max_value=100.0, step=0.1)
        comentarios = st.text_area("Comentarios", placeholder="Analisis de causa de incumplimiento")

    enviado = st.form_submit_button("Guardar")

    if enviado:
        try:
            insert_query = text("""
                INSERT INTO avances (proceso, indicador, unidad, frecuencia, meta, anio, mes, avance, comentarios)
                VALUES (:proceso, :indicador, :unidad, :frecuencia, :meta, :anio, :mes, :avance, :comentarios)
            """)
            with engine.connect() as conn:
                conn.execute(insert_query, {
                    "proceso": proceso,
                    "indicador": indicador,
                    "unidad": unidad,
                    "frecuencia": frecuencia,
                    "meta": meta,
                    "anio": anio,
                    "mes": mes,
                    "avance": avance,
                    "comentarios": comentarios
                })
                conn.commit()
            st.success("✅ Avance guardado correctamente.")
        except Exception as e:
            st.error(f"❌ Error al guardar: {e}")