import streamlit as st
import pandas as pd
import plotly.express as px
from core import data_manager, business_logic

st.set_page_config(page_title="Dashboard Ejecutivo - Gerencia", layout="wide")

st.title("🏢 Panel Ejecutivo de Gerencia")
st.markdown("Consolidado estratégico para la toma de decisiones comerciales y financieras.")

# Carga de datos
df_mkt = data_manager.cargar_marketing()
df_ventas = data_manager.cargar_ventas()
df_finanzas = data_manager.cargar_finanzas()

kpis = business_logic.calcular_resumen_gerencial(df_mkt, df_ventas, df_finanzas)

# 1. Indicadores Financieros Clave
st.subheader("1. Indicadores Financieros Globales")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Ingresos Netos", f"S/ {kpis['ventas_netas']:,.2f}")
col2.metric("Egresos Totales", f"S/ {kpis['egresos_totales']:,.2f}", delta_color="inverse")
col3.metric(
    "Utilidad Operativa", 
    f"S/ {kpis['utilidad_operativa']:,.2f}",
    delta=f"{kpis['margen_operativo']:.1f}% Margen",
    delta_color="normal" if kpis['utilidad_operativa'] >= 0 else "inverse"
)
col4.metric("Margen Operativo", f"{kpis['margen_operativo']:.1f}%", "Meta mín: 15.0%")

# 2. Indicadores Cruzados de Eficiencia
st.subheader("2. Eficiencia del Embudo Comercial (Marketing ➔ Ventas)")
col_e1, col_e2, col_e3, col_e4 = st.columns(4)
col_e1.metric("Leads Totales", f"{int(kpis['total_leads']):,}")
col_e2.metric("Unidades Vendidas", f"{kpis['total_unidades']} inmuebles")
col_e3.metric("Tasa de Conversión", f"{kpis['conversion_leads_pct']:.2f}%")
col_e4.metric("Inversión Mkt por Venta", f"S/ {kpis['cac_unidad']:,.2f}")

st.divider()

# 3. Semáforo Inteligente y Guía para Toma de Decisiones
st.subheader("3. Diagnóstico y Toma de Decisiones")
UMBRAL_MINIMO = 15.0

if kpis['ventas_netas'] == 0:
    st.info("ℹ️ **Sin operaciones:** No hay transacciones registradas en el periodo actual.")
elif kpis['margen_operativo'] < 0:
    st.error("🚨 **Pérdida Operativa:** Los gastos superan los ingresos.")
    st.markdown("**Acciones recomendadas:** Congelar contrataciones inmediatas, reducir gasto no esencial en Finanzas y revisar el retorno por canal en Marketing.")
elif kpis['margen_operativo'] < UMBRAL_MINIMO:
    st.warning(f"⚠️ **Margen Crítico ({kpis['margen_operativo']:.1f}%):** Por debajo del 15% corporativo.")
    st.markdown("**Acciones recomendadas:** Ajustar el límite de descuentos en el módulo de Ventas y optimizar presupuesto en canales publicitarios de bajo rendimiento.")
else:
    st.success(f"✅ **Operación Saludable ({kpis['margen_operativo']:.1f}%):** Cumple con los objetivos de rentabilidad.")
    st.markdown("**Acciones recomendadas:** Mantener el ritmo comercial y evaluar reinversión en los canales de marketing más eficientes.")

st.divider()

# 4. Gráficos Ejecutivos
st.subheader("4. Análisis Visual de Resultados")
col_g1, col_g2 = st.columns(2)

with col_g1:
    df_balance = pd.DataFrame({
        "Concepto": ["Ingresos Netos", "Egresos Totales", "Utilidad Operativa"],
        "Monto": [kpis["ventas_netas"], kpis["egresos_totales"], max(0, kpis["utilidad_operativa"])],
        "Tipo": ["Entrada", "Salida", "Beneficio"]
    })
    fig_balance = px.bar(
        df_balance, x="Concepto", y="Monto", color="Tipo", text_auto=".2s",
        title="Balance General: Entradas vs Salidas",
        color_discrete_map={"Entrada": "#2ca02c", "Salida": "#d62728", "Beneficio": "#1f77b4"}
    )
    st.plotly_chart(fig_balance, use_container_width=True)

with col_g2:
    df_desglose = pd.DataFrame({
        "Rubro": ["Marketing (Publicidad)", "Finanzas (Operativos/Planilla)"],
        "Monto": [kpis["inversion_mkt"], kpis["gastos_operativos"]]
    })
    fig_desglose = px.pie(
        df_desglose, names="Rubro", values="Monto", hole=0.45,
        title="Desglose de Costos de la Empresa",
        color_discrete_sequence=["#ff7f0e", "#17becf"]
    )
    st.plotly_chart(fig_desglose, use_container_width=True)