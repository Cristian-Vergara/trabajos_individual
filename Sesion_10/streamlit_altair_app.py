
import os #para manejar rutas de archivos
import io #permite crear flujos de texto/binarios en memoria (en lugar de archivos físicos)
import pandas as pd   #para manipulación y análisis de datos
import streamlit as st #para crear aplicaciones web interactivas
import altair as alt #genera los gráficos interactivos dentro de Streamlit

# ---------- Page config ----------
st.set_page_config(
    page_title="Streamlit + Altair Demo", #Título de la página
    page_icon="📊",  #emoji que acompañara al titulo
    layout="wide" # usa todo el ancho de la pantalla en vez de un diseño centrado
)

@st.cache_data  # Streamlit guarda en caché el resultado de la función, asi no recarga el CSV cada vez que se actualiza un filtro
def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["date"]) #leer el archivo y convierte la columna date a formato datetime
    # Ensure categorical ordering for nicer charts
    df["category"] = pd.Categorical(df["category"], categories=sorted(df["category"].unique()), ordered=True)  #convierte category en tipo categórico con orden alfabético
    df["region"] = pd.Categorical(df["region"], categories=sorted(df["region"].unique()), ordered=True) #convierte region en tipo categórico con orden alfabético
    return df  # devuelve el DataFrame

DATA_PATH = os.path.join(os.path.dirname(__file__), "raw_data/sales_demo.csv")# os.path.dirname(__file__) obtiene la carpeta donde está este script.
# os.path.join(..., "raw_data/sales_demo.csv") construye la ruta al archivo.
df = load_data(DATA_PATH) #carga y prepara el dataframe

# ---------- Sidebar filters ---------- (Filtros de la barra lateral) ----------
# se crea un panel lateral con tres tipos de filtros: rango de fechas, categorías y regiones
st.sidebar.header("Filters")
min_date, max_date = df["date"].min(), df["date"].max()
date_range = st.sidebar.date_input("Date range", value=(min_date, max_date), min_value=min_date, max_value=max_date)

cats = st.sidebar.multiselect("Category", options=list(df["category"].cat.categories), default=list(df["category"].cat.categories))
regs = st.sidebar.multiselect("Region", options=list(df["region"].cat.categories), default=list(df["region"].cat.categories))

# ---------- Filtered data ---------- (Datos filtrados) ----------
# se crea una mascara booleana que combina tres condiciones: Fecha dentro del rango seleccionado, Categorias incluidas en cats y Regiones incluidas en regs.
# Luego se aplica el filtro y se carga el resultado
mask = (
    (df["date"].between(pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])))
    & (df["category"].isin(cats))
    & (df["region"].isin(regs))
)
fdf = df.loc[mask].copy()

# ---------- KPIs ---------- (Indicadores clave de rendimiento) ----------
# Divide la pagina en tres columnas (col1, col2, col3) y muestra en cada una un KPI diferente
# Muestra tres metricas: Total de ingresos, Total de unidades vendidas y precio promedio
col1, col2, col3 = st.columns(3)
col1.metric("Total revenue", f"${fdf['revenue'].sum():,.0f}")
col2.metric("Total units", f"{fdf['units'].sum():,.0f}")
col3.metric("Average price", f"${fdf['price'].mean():.2f}")

st.markdown("---")

# ---------- Altair charts ---------- (gráficos de Altair) ----------
# Global selection for crossfiltering
selection = alt.selection_point(fields=["category", "region"], bind="legend") #define una selección interactiva que permitirá filtrar los gráficos al hacer clic en la leyenda.

# Line chart over time
# Usa mark_line() para graficar los ingresos por fecha 
# Ejes: fecha(x) y suma de ingresos(y)
# Colores por categoria
#
line = (
    alt.Chart(fdf)
    .mark_line(point=True)
    .encode(
        x=alt.X("date:T", title="Date"),
        y=alt.Y("sum(revenue):Q", title="Revenue"),
        color=alt.Color("category:N", title="Category"),
        tooltip=[alt.Tooltip("date:T"), alt.Tooltip("sum(revenue):Q", title="Revenue", format=",.0f")] #muestra detalles al pasar el mouse 
    )
    .add_params(selection) #permite que la selección interactiva afecte este gráfico
    .transform_filter(selection) #filtra los datos según la selección
    .properties(title="Revenue over time") #título del gráfico
)

# Bar by category (grafico de barras por categoría)
# Usa mark_bar() para graficar los ingresos por categoría
# Ejes: categoría(y) y suma de ingresos(x)
# Colores por categoría
# Muestra ingresos totales por categoría, ordenados de mayor a menor
bar_cat = (
    alt.Chart(fdf)
    .mark_bar()
    .encode(
        x=alt.X("sum(revenue):Q", title="Revenue"),
        y=alt.Y("category:N", sort="-x", title="Category"),
        color=alt.Color("category:N", legend=None),
        tooltip=[alt.Tooltip("sum(revenue):Q", title="Revenue", format=",.0f")]
    )
    .add_params(selection)
    .transform_filter(selection)
    .properties(title="Revenue by category")
)

# Bar by region (grafico de barras por región)
# Usa mark_bar() para graficar los ingresos por región
# Ejes: región(y) y suma de ingresos(x)
# Colores por región
# Muestra ingresos totales por región, ordenados de mayor a menor
#igual que el anterior pero por región
bar_reg = (
    alt.Chart(fdf)
    .mark_bar()
    .encode(
        x=alt.X("sum(revenue):Q", title="Revenue"),
        y=alt.Y("region:N", sort="-x", title="Region"),
        color=alt.Color("region:N", legend=None),
        tooltip=[alt.Tooltip("sum(revenue):Q", title="Revenue", format=",.0f")]
    )
    .add_params(selection)
    .transform_filter(selection)
    .properties(title="Revenue by region")
)

# Layout (Diseño)
upper = line.properties(height=320).resolve_scale(color="independent")  # gráfico de líneas en la parte superior
lower = alt.hconcat(bar_cat, bar_reg).resolve_scale(color="independent") #dos graficos de barras lado a lado en la parte inferior con cada grafico manejando su propia escala de color

st.altair_chart(upper, use_container_width=True) #renderiza los graficos en la app
st.altair_chart(lower, use_container_width=True) #renderiza los graficos en la app

st.markdown("---")

# ---------- Data table and download ---------- (Tabla de datos y descarga) ----------
# muestra el dataset filtrado dentro de un contenedor expandible
with st.expander("Show filtered data"):
    st.dataframe(fdf, use_container_width=True, height=300)

# función para convertir el DataFrame filtrado a bytes en formato CSV en memoria (sin guardarlo en disco)
# st.download_button genera un botón para descargar ese CSV.
def to_csv_bytes(df: pd.DataFrame) -> bytes:
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    return buf.getvalue().encode("utf-8")

st.download_button(
    label="Download filtered data (CSV)",
    data=to_csv_bytes(fdf),
    file_name="filtered_data.csv",
    mime="text/csv"
)

st.caption("Built with Streamlit + Altair · Demo app for teaching analytics.") #muestra un texto aclaratorio o de crédito al final
