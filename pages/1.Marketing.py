import streamlit as st
import pandas as pd
import plotly.express as px
import sys
import os

# Permitir importaciones desde la carpeta core/
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from core import data_manager

st.set_page_config(page_title="Gestión de Marketing", layout="wide")

st.title("📢 Dashboard 1: Marketing y Captación de Prospectos")
st.markdown("Registro transaccional de campañas publicitarias e inversión comercial.")

# 1. Cargar datos desde la capa de persistencia
df_marketing = data_manager.cargar_marketing()

# 2. Interfaz CRUD con st.data_editor
st.subheader("Control de Presupuesto y Leads por Canal")
st.caption("💡 Haz doble clic para editar valores, añade filas al final o selecciona una fila y presiona 'Supr' para eliminar.")

df_editado = st.data_editor(
    df_marketing,
    num_rows="dynamic",
    use_container_width=True,
    key="editor_marketing"
)

# Botón para persistir cambios
col_btn, _ = st.columns([1, 4])
with col_btn:
    if st.button("💾 Guardar Cambios", use_container_width=True):
        data_manager.guardar_marketing(df_editado)
        st.success("¡Registros de marketing guardados correctamente!")

st.divider()

# 3. Lógica de negocio y métricas clave
if not df_editado.empty:
    total_inversion = df_editado["Presupuesto"].sum()
    total_leads = df_editado["Leads"].sum()
    cpl_promedio = (total_inversion / total_leads) if total_leads > 0 else 0.0

    # Tarjetas ejecutivas (KPI Cards)
    col1, col2, col3 = st.columns(3)
    col1.metric("Presupuesto Total Invertido", f"S/ {total_inversion:,.2f}")
    col2.metric("Total Leads Captados", f"{int(total_leads):,}")
    col3.metric("Costo por Lead (CPL) Promedio", f"S/ {cpl_promedio:,.2f}")

    # 4. Visualización con Plotly Express
    st.subheader("Rendimiento por Canal Publicitario")
    fig = px.bar(
        df_editado,
        x="Canal",
        y="Presupuesto",
        color="Leads",
        text="Leads",
        title="Inversión vs. Captación de Leads",
        labels={"Presupuesto": "Inversión (S/)", "Leads": "Prospectos"},
        color_continuous_scale="Blues"
    )
    fig.update_layout(xaxis_title="Canal", yaxis_title="Inversión en Soles")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("No hay registros disponibles. Agrega al menos un canal en la tabla superior.")