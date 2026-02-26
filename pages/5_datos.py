import streamlit as st
import pandas as pd
import psycopg2
from sqlalchemy import create_engine, text
from psycopg2.extras import RealDictCursor

# --- CONFIGURACIÓN DE CONEXIÓN ---
DB_USER = "postgres"
DB_PASSWORD = "1234"
DB_HOST = "localhost"
DB_PORT = "5432" 
DB_NAME = "avances_iso"

# --- CADENA DE CONEXIÓN PARA POSTGRESQL ---
engine = create_engine(f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

# --- FUNCIÓN DE CONEXIÓN (AGREGA ESTO) ---
def get_connection():
    """Crea y retorna una conexión a PostgreSQL"""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        return conn
    except Exception as e:
        st.error(f"Error conectando a la base de datos: {e}")
        return None

# Configuracion de la pagina (En el productivo se llama "3_Consulta.py")

st.title("📊 Consulta de registros")

#  OBTENER OPCIONES PARA LOS SELECTBOX

def obtener_opciones(columna):
    conn = get_connection()
    cur = conn.cursor()

    query = f"SELECT DISTINCT {columna} FROM avances ORDER BY {columna}"
    cur.execute(query)

    valores = [row[0] for row in cur.fetchall() if row[0] not in (None, "")]
    
    cur.close()
    conn.close()

    return valores

# Obtener indicadores por procesos 
def obtener_indicadores_por_proceso(proceso):
    conn = get_connection()
    cur = conn.cursor()

    if not proceso:
        query = """
            SELECT DISTINCT indicador
            FROM avances
            ORDER BY indicador
        """
        cur.execute(query)
    else:
        query = """
            SELECT DISTINCT indicador
            FROM avances
            WHERE proceso = %s
            ORDER BY indicador
        """
        cur.execute(query, (proceso,))

    indicadores = [row[0] for row in cur.fetchall() if row[0] not in (None, "")]
    
    cur.close()
    conn.close()
    return indicadores

#  CONSULTA FILTRADA

def consultar_avances(proceso, indicador, anio, mes):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    query = """
        SELECT id, proceso, indicador, unidad, frecuencia, meta, anio, mes,
               avance, comentarios, fecha_registro
        FROM avances
        WHERE 1=1
    """
    params = {}

    if proceso and proceso != "":
        query += " AND proceso = %(proceso)s"
        params["proceso"] = proceso

    if indicador and indicador != "":
        query += " AND indicador = %(indicador)s"
        params["indicador"] = indicador

    if anio and anio != "Todo":
        query += " AND anio = %(anio)s"
        params["anio"] = anio

    if mes and mes != "Todo":
        query += " AND mes = %(mes)s"
        params["mes"] = mes

    cur.execute(query, params)
    rows = cur.fetchall()

    cur.close()
    conn.close()
    return rows


#      INTERFAZ STREAMLIT

st.set_page_config(page_title="Consulta de Avances ISO", page_icon="📊", layout="centered")

# Cargar opciones desde la BD
opciones_proceso = [""] + obtener_opciones("proceso")
opciones_indicador = [""] + obtener_opciones("indicador")
opciones_anio = ["Todo"] + obtener_opciones("anio")
opciones_mes = ["Todo"] + obtener_opciones("mes")


# --- Filtros ---

procesos = obtener_opciones("proceso")

proceso = st.selectbox(
    "Proceso",
    options=procesos,
    index=None,
    placeholder="Selecciona el proceso"
)

indicadores = obtener_indicadores_por_proceso(proceso)

indicador = st.selectbox(
    "Indicador",
    options=indicadores,
    index=None,
    placeholder="Selecciona el indicador",
    disabled=not proceso
)


# Año y Mes (se quedan como tú los tienes)
anio = st.selectbox("Año:", opciones_anio)
mes = st.selectbox("Mes:", opciones_mes)

# Botón
buscar = st.button("Buscar")


#     LÓGICA DEL BOTÓN

if buscar:
    resultados = consultar_avances(proceso, indicador, anio, mes)

    if not resultados:
        st.warning("⚠ No se encontraron registros con los filtros seleccionados.")
    else:
        st.success(f"🔍 Se encontraron {len(resultados)} registros.")

        # --- TARJETAS HTML ---
        for r in resultados:
            fecha = r["fecha_registro"].strftime("%Y-%m-%d %H:%M")
            card = f"""
            <div style="
                padding: 15px;
                background-color: #F8F9FA;
                margin-bottom: 15px;
                border-radius: 10px;
                box-shadow: 0 3px 8px rgba(0,0,0,0.1);
            ">
                <h4 style="margin:0;">📌 {r['proceso']}</h4>
                <p><b>Indicador:</b> {r['indicador']}</p>
                <p><b>Año:</b> {r['anio']}  |  <b>Mes:</b> {r['mes']}</p>
                <p><b>Meta:</b> {r['meta']}  | <b>Avance:</b> {r['avance']}</p>
                <p><b>Fecha de registro:</b> {fecha}</p>
                <p><b>Comentarios:</b> {r['comentarios']}</p>
            </div>
            """
            st.markdown(card, unsafe_allow_html=True)
