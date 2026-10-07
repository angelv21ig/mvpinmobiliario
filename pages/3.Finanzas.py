import streamlit as st
import pandas as pd
import plotly.express as px
import sys
import os

# Permitir importaciones desde la carpeta core/
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from core import data_manager

st.set_page_config(page_title="Gestión de Finanzas", layout="wide")

st.title("📊 Dashboard 3: Finanzas y Estructura de Costos")
st.markdown("Registro y clasificación transaccional de costos operativos y egresos comerciales.")

# 1. Cargar datos desde la capa de persistencia
df_finanzas = data_manager.cargar_finanzas()

# 2. Interfaz CRUD con st.data_editor
st.subheader("Control de Egresos Operativos")
st.caption("💡 Modifica montos o tipos (Fijo/Variable), añade nuevas categorías al final o selecciona una fila y pulsa 'Supr' para borrar.")

# Configuración de columnas para asegurar selectores limpios
df_editado = st.data_editor(
    df_finanzas,
    num_rows="dynamic",
    use_container_width=True,
    key="editor_finanzas",
    column_config={
        "Tipo": st.column_config.SelectboxColumn(
            "Tipo de Costo",
            help="Selecciona si el costo es fijo o variable",
            options=["Fijo", "Variable"],
            required=True
        ),
        "Monto": st.column_config.NumberColumn(
            "Monto Asignado (S/)",
            min_value=0.0,
            format="S/ %.2f"
        )
    }
)

# Botón para persistir cambios
col_btn, _ = st.columns([1, 4])
with col_btn:
    if st.button("💾 Guardar Cambios", use_container_width=True):
        data_manager.guardar_finanzas(df_editado)
        st.success("¡Estructura de costos guardada correctamente!")

st.divider()

# 3. Lógica de negocio y métricas clave
if not df_editado.empty:
    total_gastos = df_editado["Monto"].sum()
    
    # Separación por tipo de costo
    gastos_fijos = df_editado[df_editado["Tipo"] == "Fijo"]["Monto"].sum()
    gastos_variables = df_editado[df_editado["Tipo"] == "Variable"]["Monto"].sum()
    
    pct_fijos = (gastos_fijos / total_gastos * 100) if total_gastos > 0 else 0.0
    pct_variables = (gastos_variables / total_gastos * 100) if total_gastos > 0 else 0.0

    # Tarjetas ejecutivas (KPI Cards)
    col1, col2, col3 = st.columns(3)
    col1.metric("Egresos Totales Operativos", f"S/ {total_gastos:,.2f}")
    col2.metric("Gastos Fijos", f"S/ {gastos_fijos:,.2f}", f"{pct_fijos:.1f}% del total")
    col3.metric("Gastos Variables", f"S/ {gastos_variables:,.2f}", f"{pct_variables:.1f}% del total")

    # 4. Visualización con Plotly Express
    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        st.subheader("Distribución por Categoría")
        fig_cat = px.pie(
            df_editado,
            names="Categoria",
            values="Monto",
            hole=0.4,
            title="Participación de Gastos por Categoría",
            color_discrete_sequence=px.colors.sequential.Teal
        )
        st.plotly_chart(fig_cat, use_container_width=True)

    with col_chart2:
        st.subheader("Estructura Fijo vs. Variable")
        df_tipo = pd.DataFrame({
            "Tipo": ["Fijo", "Variable"],
            "Monto": [gastos_fijos, gastos_variables]
        })
        fig_tipo = px.bar(
            df_tipo,
            x="Tipo",
            y="Monto",
            text_auto=".2s",
            color="Tipo",
            title="Comparativo de Costos Fijos vs Variables",
            color_discrete_map={"Fijo": "#2b5c8f", "Variable": "#d95f02"}
        )
        st.plotly_chart(fig_tipo, use_container_width=True)
else:
    st.warning("No hay registros de costos disponibles. Agrega al menos un gasto en la tabla superior.")