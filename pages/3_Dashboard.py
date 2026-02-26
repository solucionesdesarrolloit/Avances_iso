import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv
import matplotlib.pyplot as plt
import seaborn as sns

# --- CONFIGURACIÓN DE CONEXIÓN ---
DB_USER = "postgres"
DB_PASSWORD = "1234"
DB_HOST = "localhost"
DB_PORT = "5432" 
DB_NAME = "avances_iso"

# --- CADENA DE CONEXIÓN PARA POSTGRESQL ---
engine = create_engine(f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

st.set_page_config(page_title="Dashboards", layout="wide")
st.title("📊 Indicadores")

# -- Nuevo -- #


# Ejecutar consulta y cargar datos en un DataFrame
query = "SELECT * FROM avances;"

with engine.connect() as conn:
    df = pd.read_sql_query(query, conn)

# Mostrar tabla de datos
#st.dataframe(df.head())

fig, ax = plt.subplots(figsize=(5,3))  # más pequeña

sns.barplot(data=df, x='proceso', y='avance', ci=None, ax=ax)
col1, col2 = st.columns([1, 2])  # col1 es más angosta


# Título y etiquetas más pequeñas
ax.set_title("Avance anual promedio por proceso", fontsize=8)
ax.set_xlabel("Proceso", fontsize=7)
ax.set_ylabel("Avance promedio", fontsize=7)

# Ejes más compactos
plt.xticks(rotation=45, fontsize=6)
plt.yticks(fontsize=6)

with col1:
    st.pyplot(fig, use_container_width=True)

# Margen extra para que no se corte el texto
plt.tight_layout()

#st.pyplot(fig)