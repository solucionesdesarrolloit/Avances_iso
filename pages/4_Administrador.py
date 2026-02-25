import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

# --- CONFIGURACIÓN DE CONEXIÓN ---
DB_USER = "root"
DB_PASSWORD = "Pass1234"
DB_HOST = "127.0.0.1"
DB_PORT = "3306"  # Puerto por defecto de MySQL
DB_NAME = "avances_ISO"

# --- CADENA DE CONEXIÓN PARA MYSQL ---
engine = create_engine(f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Administrador", layout="wide")

# --- AUTENTICACIÓN SIMPLE ---
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
    st.rerun()

if not st.session_state.autenticado:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        password = st.text_input("🔐 Panel de Administración", type="password")
        if st.button("Entrar"):
            if password == "Admin123":
                st.session_state.autenticado = True
            else:
                st.error("Contraseña incorrecta ❌")

# --- CONTENIDO DEL ADMINISTRADOR ---
if st.session_state.autenticado:
    st.title("🛠 Administrador")

    # --- CONSULTAR OPCIONES EXISTENTES ---
    try:
        unidades_df = pd.read_sql("SELECT nombre FROM unidades", engine)
        frecuencias_df = pd.read_sql("SELECT nombre FROM frecuencias", engine)
        metas_df = pd.read_sql("SELECT valor FROM metas", engine)
    except Exception as e:
        st.error(f"No se pudieron cargar las opciones: {e}")
        st.stop()

    unidades = unidades_df["nombre"].tolist()
    frecuencias = frecuencias_df["nombre"].tolist()
    metas = metas_df["valor"].tolist()

    # ==============================================================
    # --- FORMULARIO PARA AGREGAR NUEVA COMBINACIÓN ---
    # ==============================================================
    procesos_df = pd.read_sql(
    "SELECT DISTINCT proceso FROM combinaciones_base ORDER BY proceso",
    engine
)
    procesos = procesos_df["proceso"].tolist()

    st.header("Agregar nuevo proceso/indicador")
    with st.form("form_combinacion"):
        col1, col2 = st.columns(2)

        with col1:
            proceso_existente = st.selectbox(
                "Proceso existente (opcional)",
                options=["Selecciona proceso existente"] + procesos
        )

            proceso_nuevo = st.text_input(
                "Nuevo proceso (si no existe)"
        )

            indicador = st.text_input("Indicador")

        with col2:
            unidad = st.selectbox("Unidad de negocio", unidades)
            frecuencia = st.selectbox("Frecuencia", frecuencias)
            meta = st.selectbox("Meta", metas)

        guardar = st.form_submit_button("Guardar")

        if guardar:
            # decidir cuál proceso usar
            if proceso_nuevo.strip():
                proceso = proceso_nuevo.strip().title()
            elif proceso_existente != "— Nuevo proceso —":
                proceso = proceso_existente
            else:
                proceso = ""

            indicador = indicador.strip()

            if not proceso or not indicador:
                st.warning("❌ Debes completar Proceso e Indicador")
            else:
                try:
                    insert_query = text("""
                        INSERT INTO combinaciones_base 
                        (proceso, indicador, unidad, frecuencia, meta)
                        VALUES (:proceso, :indicador, :unidad, :frecuencia, :meta)
                    """)
                    with engine.connect() as conn:
                        conn.execute(insert_query, {
                            "proceso": proceso,
                            "indicador": indicador,
                            "unidad": unidad,
                            "frecuencia": frecuencia,
                            "meta": meta
                        })
                        conn.commit()
                    st.success("✅ Indicador guardado correctamente.")
                except Exception as e:
                    st.error(f"❌ Error al guardar: {e}")


    # --- MODIFICAR / ELIMINAR COMBINACIONES EXISTENTES ---

    st.text("\n")
    st.subheader("Modificar / Eliminar Indicadores existentes")
    try:
        combinaciones_df = pd.read_sql("SELECT * FROM combinaciones_base", engine)
    except Exception as e:
        st.error(f"No se pudieron cargar las combinaciones: {e}")
        st.stop()

    # Configuración del editor con selectboxes
    editable_df = combinaciones_df[["id", "proceso", "indicador", "unidad", "frecuencia", "meta"]]
    column_config = {
        "unidad": st.column_config.SelectboxColumn("Unidad de negocio", options=unidades),
        "frecuencia": st.column_config.SelectboxColumn("Frecuencia", options=frecuencias),
        "meta": st.column_config.NumberColumn("Meta", format="%d")  # muestra ceros
        #"meta": st.column_config.SelectboxColumn("Meta", options=metas)
    }

    edited_df = st.data_editor(
        editable_df,
        num_rows="dynamic",
        use_container_width=True,
        key="editor",
        column_config=column_config
    )

    if st.button("Guardar cambios"):
        try:
            with engine.connect() as conn:
                for _, row in edited_df.iterrows():
                    update_query = text("""
                        UPDATE combinaciones_base
                        SET proceso=:proceso, indicador=:indicador, unidad=:unidad,
                            frecuencia=:frecuencia, meta=:meta
                        WHERE id=:id
                    """)
                    conn.execute(update_query, {
                        "id": row["id"],
                        "proceso": row["proceso"],
                        "indicador": row["indicador"],
                        "unidad": row["unidad"],
                        "frecuencia": row["frecuencia"],
                        "meta": row["meta"]
                    })
                conn.commit()
            st.success("✅ Todos los cambios guardados correctamente.")
        except Exception as e:
            st.error(f"❌ Error al guardar cambios: {e}")

    st.write("Eliminar procesos/indicadores seleccionados")
    delete_ids = st.multiselect(
        "Selecciona los ID a eliminar",
        options=combinaciones_df["id"].tolist()
    )
    if st.button("Eliminar seleccionados"):
        if delete_ids:
            try:
                delete_query = text("DELETE FROM combinaciones_base WHERE id IN :ids")
                with engine.connect() as conn:
                    conn.execute(delete_query, {"ids": tuple(delete_ids)})
                    conn.commit()
                st.success("🗑 Eliminado correctamente.")
            except Exception as e:
                st.error(f"❌ Error al eliminar: {e}")
        else:
            st.warning("❌ No seleccionaste nada para eliminar")

    # ==============================================================
    # --- ELIMINAR REGISTROS DE 'AVANCES' ---
    # ==============================================================
    st.subheader("🗑 Eliminar registros de avances")

    try:
        avances_df = pd.read_sql("""
            SELECT id, proceso, unidad, indicador, anio as año, mes, meta, avance, comentarios, fecha_registro
            FROM avances
            ORDER BY fecha_registro DESC
        """, engine)
    except Exception as e:
        st.error(f"No se pudieron cargar los registros de avances: {e}")
        st.stop()

    st.dataframe(avances_df, use_container_width=True, height=400)

    delete_ids_avances = st.multiselect(
        "Selecciona los registros a eliminar (por ID)",

        options=avances_df["id"].tolist()
    )

    if st.button("Eliminar registros"):
        if delete_ids_avances:
            try:
                delete_query = text("DELETE FROM avances WHERE id IN :ids")
                with engine.connect() as conn:
                    conn.execute(delete_query, {"ids": tuple(delete_ids_avances)})
                    conn.commit()
                st.success("✅ Registros de avances eliminados correctamente.")
            except Exception as e:
                st.error(f"❌ Error al eliminar: {e}")
        else:
            st.warning("❌ No seleccionaste ningún registro para eliminar")
            