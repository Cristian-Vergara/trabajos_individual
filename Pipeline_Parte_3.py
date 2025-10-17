"""
App Streamlit para mostrar y editar datos de la tabla global_land_temperatures_by_country en PostgreSQL
"""

import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError

# Configuración de la página
st.set_page_config(page_title="Temperaturas Globales por País", layout="wide")
st.title("🌍 Temperaturas Globales por País")

# Parámetros de conexión a PostgreSQL
usuario = 'wiwi'
clave = 'prymus11'
host = 'localhost'
puerto = '5432'
db = 'practica'
tabla = 'global_land_temperatures_by_country'
st.subheader(f"Hola, {usuario}")
conexion_str = f'postgresql+psycopg2://{usuario}:{clave}@{host}:{puerto}/{db}'

# Leer los datos de la tabla
try:
    engine = create_engine(conexion_str)
    df = pd.read_sql_table(tabla, engine)
    st.success(f"Datos obtenidos de '{tabla}' en PostgreSQL.")
except SQLAlchemyError as e:
    st.error(f"Error al conectar o leer la tabla: {e}")
    st.stop()

# Mostrar la tabla editable
st.write("### puedes cambiar los datos directamente de la tabla:")
edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)

# Botón para guardar cambios en la base de datos
if st.button("Guardar cambios en PostgreSQL"):
    try:
        # Sobrescribe la tabla con los datos editados
        edited_df.to_sql(tabla, engine, if_exists='replace', index=False)
        st.success("¡Cambios guardados exitosamente en PostgreSQL!")
    except SQLAlchemyError as e:
        st.error(f"Error al guardar los cambios: {e}")

# Ejecutar la aplicación Streamlit
# streamlit run Pipeline_Parte_3.py