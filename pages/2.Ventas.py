import streamlit as st
import pandas as pd
import plotly.express as px
import sys
import os

# Permitir importaciones desde la carpeta core/
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from core import data_manager

st.set_page_config(page_title="Gestión de Ventas", layout="wide")

st.title("💰 Dashboard 2: Ventas y Comercialización Inmobiliaria")
st.markdown("Registro transaccional de colocaciones inmobiliarias y operaciones de venta.")

# 1. Cargar datos desde la capa de persistencia
df_ventas = data_manager.cargar_ventas()

# 2. Interfaz CRUD con st.data_editor
st.subheader("Registro de Operaciones por Proyecto / Unidad")
st.caption("💡 Edita directamente los valores en la tabla, agrega filas al final o selecciona una fila y pulsa 'Supr' para borrar.")

df_editado = st.data_editor(
    df_ventas,
    num_rows="dynamic",
    use_container_width=True,
    key="editor_ventas"
)

# Botón para persistir cambios
col_btn, _ = st.columns([1, 4])
with col_btn:
    if st.button("💾 Guardar Cambios", use_container_width=True):
        data_manager.guardar_ventas(df_editado)
        st.success("¡Registros de ventas guardados correctamente!")

st.divider()

# 3. Lógica de negocio y métricas clave
if not df_editado.empty:
    # Cálculo de columnas derivadas
    descuento_monto = df_editado["Venta_Bruta"] * (df_editado["Descuento_Pct"] / 100)
    venta_neta = df_editado["Venta_Bruta"] - descuento_monto
    
    total_bruto = df_editado["Venta_Bruta"].sum()
    total_descuentos = descuento_monto.sum()
    total_neto = venta_neta.sum()
    unidades_colocadas = len(df_editado)

    # Tarjetas ejecutivas (KPI Cards)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Ingresos Netos Totales", f"S/ {total_neto:,.2f}")
    col2.metric("Unidades Colocadas", f"{unidades_colocadas} inmuebles")
    col3.metric("Venta Bruta Total", f"S/ {total_bruto:,.2f}")
    col4.metric("Descuentos Aplicados", f"S/ {total_descuentos:,.2f}")

    # Dataframe auxiliar para visualización
    df_plot = df_editado.copy()
    df_plot["Venta_Neta"] = venta_neta

    # 4. Visualización con Plotly Express
    st.subheader("Ingresos Netos por Proyecto / Inmueble")
    fig = px.bar(
        df_plot,
        x="Proyecto",
        y="Venta_Neta",
        text_auto=".2s",
        title="Distribución de Ventas Netas por Unidad",
        labels={"Proyecto": "Inmueble / Unidad", "Venta_Neta": "Ingreso Neto (S/)"},
        color="Venta_Neta",
        color_continuous_scale="Greens"
    )
    fig.update_layout(xaxis_title="Proyecto", yaxis_title="Venta Neta en Soles")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("No hay registros de ventas disponibles. Agrega al menos una operación en la tabla superior.")