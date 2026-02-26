import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

# Carga el .env
load_dotenv()  

# --- CONFIGURACIÓN DE CONEXIÓN ---
DB_USER = "postgres"
DB_PASSWORD = "1234"
DB_HOST = "localhost"
DB_PORT = "5432" 
DB_NAME = "avances_iso"

# --- CADENA DE CONEXIÓN PARA POSTGRESQL ---
engine = create_engine(f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

st.set_page_config(page_title="Ver Datos", layout="wide")
st.title("📊 Registros")

# --- CONSULTA ---
try:
    with engine.connect() as conn:
        df = pd.read_sql("""SELECT 
                                anio AS "Año",
                                proceso AS "Proceso",
                                unidad,
                                indicador,
                                ROUND(AVG(meta), 2) AS "Meta",
                                ROUND(AVG(avance), 2) AS "Anual",
                                CASE 
                                WHEN ROUND(AVG(avance), 2) > ROUND(AVG(meta), 2) THEN 'Correcto'
                                ELSE 'Incorrecto'
                                END AS "Estatus"
                            FROM avances
                            GROUP BY anio, proceso, unidad, indicador
                            ORDER BY proceso;
    """, conn)

        # Renombrar columnas solo para mostrar al usuario
        df = df.rename(columns={"anio": "Año"})
        df = df.rename(columns={"unidad": "Unidad de negocio"})


        st.dataframe(df, use_container_width=True, height=600)
except Exception as e:
    st.error(f"❌ Error al cargar los datos: {e}")
