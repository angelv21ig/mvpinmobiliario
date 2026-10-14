from datetime import date
import os
import sys
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Permitir importaciones desde la carpeta core/
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from core import cso_logic, data_manager

st.set_page_config(
    page_title="Dashboard Comercial CSO - Ventas",
    page_icon="🏢",
    layout="wide",
)

# ==============================================================================
# 1. CARGA DE DATOS DESDE LA CAPA DE PERSISTENCIA (DATA_MANAGER)
# ==============================================================================
data_manager.asegurar_datos_cso()

df_ventas = data_manager.cargar_cso_ventas()
df_cotiz = data_manager.cargar_cso_cotiz()
df_leads = data_manager.cargar_cso_leads()
df_meta = data_manager.cargar_cso_meta()
df_asesores = data_manager.cargar_cso_asesores()
df_costos = data_manager.cargar_cso_costos()
df_eventos = data_manager.cargar_cso_eventos()
df_inventario = data_manager.cargar_cso_inventario()
cfg = data_manager.cargar_cso_config()

# Listas maestras para selectores limpios en tablas CRUD
LISTA_VENDEDORES = sorted(
    list(
        set(
            df_asesores["Vendedor"].dropna().astype(str).tolist()
            + ["Juan Carlos Paredes", "JeanPaul Campos", "Alfredo Caceda", "Vicente Quispe", "Jhovana", "Jose Carrillo", "Josue", "Ingrid Villegas", "Karina", "Herberth"]
        )
    )
)
LISTA_FUENTES = [
    "Publicidad pagada", "Referido", "Activación",
    "Orgánico", "Base de datos", "Redes Sociales", "tiktok"
]
LISTA_ESTADOS_VENTA = [
    "Venta", "Separado", "Listo para Comprar", "En Cotizacion", "Venta Perdida"
]
LISTA_ESTADOS_KOMMO = [
    "NO CONTESTA - por confirmar",
    "NO CONTESTA 3V",
    "REALIZAR INVITACION",
    "respondieron LLAMADA/ WHATSAPP",
    "seguimiento",
    "INTERESADo",
    "agendo oficina /presentación virtual",
    "AGENDO VISITA al proyecto",
    "ASISTIO al PROYECTO",
    "LISTO PARA COMPRAR",
]

# ==============================================================================
# 2. CABECERA Y FILTRO GLOBAL DE PERIODO
# ==============================================================================
st.title("🏢 Dashboard Comercial Inmobiliario — CSO (Chief Sales Officer)")
st.markdown(
    "Control integral de ventas, embudo comercial CRM, mix contado/financiado, "
    "cash-in, calidad financiera, productividad de asesores, inventario y eventos."
)

with st.container(border=True):
    col_f1, col_f2, col_f3, col_f4 = st.columns([1.2, 1.2, 1.6, 1.2])
    with col_f1:
        fecha_inicio = st.date_input(
            "📅 Fecha de Inicio",
            value=date(2025, 9, 30),
            key="cso_fecha_ini",
        )
    with col_f2:
        fecha_fin = st.date_input(
            "📅 Fecha de Fin",
            value=date(2026, 9, 30),
            key="cso_fecha_fin",
        )
    with col_f3:
        proyectos_disp = ["Todos"]
        if not df_ventas.empty and "Proyecto" in df_ventas.columns:
            proyectos_disp += sorted(
                df_ventas["Proyecto"].dropna().astype(str).unique().tolist()
            )
        proyecto_sel = st.selectbox(
            "🏘️ Proyecto Inmobiliario", proyectos_disp, index=0
        )
    with col_f4:
        st.metric("Fecha de Corte Análisis", fecha_fin.strftime("%d/%m/%Y"))

if fecha_inicio > fecha_fin:
    st.error("⚠️ La Fecha de Inicio no puede ser mayor que la Fecha de Fin.")
    st.stop()

# Filtrar por proyecto si se selecciona uno específico
if proyecto_sel != "Todos":
    df_v_uso = df_ventas[df_ventas["Proyecto"] == proyecto_sel].copy()
    df_c_uso = df_cotiz[df_cotiz["Proyecto"] == proyecto_sel].copy()
    df_l_uso = df_leads[df_leads["Proyecto"] == proyecto_sel].copy()
else:
    df_v_uso, df_c_uso, df_l_uso = df_ventas, df_cotiz, df_leads

# Ejecutar el motor de cálculo CSO para todo el dashboard
dash = cso_logic.calcular_dashboard_cso(
    df_ventas=df_v_uso,
    df_cotiz=df_c_uso,
    df_leads=df_l_uso,
    df_meta=df_meta,
    df_asesores=df_asesores,
    df_costos=df_costos,
    df_eventos=df_eventos,
    df_inventario=df_inventario,
    cfg=cfg,
    fecha_inicio=fecha_inicio,
    fecha_fin=fecha_fin,
)

res = dash["resultados"]
mix = dash["mix_y_caja"]
cal = dash["calidad"]
cos = dash["costos"]
inv = dash["inventario"]
eqp = dash["productividad_equipo"]
emb = dash["embudo"]
evn = dash["eventos"]
rsg = dash["riesgos"]

# ==============================================================================
# 3. NAVEGACIÓN PRINCIPAL EN 4 MÓDULOS
# ==============================================================================
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 1. Dashboard CSO (Financiero y Calidad)",
    "🎯 2. Embudo CRM, Semanal y Eventos",
    "👥 3. Productividad Asesores e Inventario",
    "📝 4. Gestión de Datos en Vivo (CRUD)",
])

# ==============================================================================
# PESTAÑA 1: DASHBOARD EJECUTIVO CSO (BLOQUES 1, 2, 3, 4 Y 11)
# ==============================================================================
with tab1:
    # --- Tarjetas de Resumen Superior ---
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric(
        "Ventas Reales Cerradas",
        f"S/ {res['ventas_reales_soles']:,.2f}",
        f"{res['ventas_reales_unid']} lotes vendidos",
    )
    k2.metric(
        "Meta del Periodo",
        f"S/ {res['meta_soles']:,.2f}",
        f"Meta: {res['meta_unidades']:.0f} lotes",
    )
    k3.metric(
        "Índice Cumplimiento",
        f"{res['indice_cumplimiento_pct']:.2f}%",
        f"Gap: S/ {res['gap_soles']:,.2f}",
        delta_color="normal" if res["gap_soles"] >= 0 else "inverse",
    )
    k4.metric(
        "Cash-in Comercial Total",
        f"S/ {cal['cash_in_total_soles']:,.2f}",
        f"{cal['cash_in_total_pct']:.1f}% de la venta (Meta 35%)",
    )
    k5.metric(
        "SCORE GLOBAL CSO",
        f"{cal['score_cso']:.2f} pts",
        f"Calidad: {cal['indice_calidad_venta']:.1f} pts",
    )

    st.divider()

    # --- BLOQUE 1: RESULTADOS COMERCIALES Y FACTURACIÓN ACUMULADA ---
    st.subheader("1. Resultados Comerciales y Facturación Acumulada")
    col_b1_left, col_b1_right = st.columns([1.35, 1])

    with col_b1_left:
        st.markdown("**Meta vs. Resultados y Pipeline del Periodo**")
        df_bloque1 = pd.DataFrame([
            {
                "Indicador": "Meta del Periodo",
                "Monto (S/)": f"S/ {res['meta_soles']:,.2f}",
                "Unidades": f"{res['meta_unidades']:.0f}",
            },
            {
                "Indicador": "Ventas Reales (Activas)",
                "Monto (S/)": f"S/ {res['ventas_reales_soles']:,.2f}",
                "Unidades": f"{res['ventas_reales_unid']}",
            },
            {
                "Indicador": "Separaciones Activas",
                "Monto (S/)": f"S/ {res['separaciones_soles']:,.2f}",
                "Unidades": f"{res['separaciones_unid']}",
            },
            {
                "Indicador": "Bolsa de Cotizaciones",
                "Monto (S/)": f"S/ {res['bolsa_cotiz_soles']:,.2f}",
                "Unidades": f"{res['bolsa_cotiz_unid']}",
            },
            {
                "Indicador": "Pipeline Ponderado (Listo p/ comprar)",
                "Monto (S/)": f"S/ {res['pipeline_pond_soles']:,.2f}",
                "Unidades": f"{res['pipeline_pond_unid']}",
            },
            {
                "Indicador": "Forecast de Cierre",
                "Monto (S/)": f"S/ {res['forecast_cierre_soles']:,.2f}",
                "Unidades": f"{res['forecast_cierre_unid']}",
            },
            {
                "Indicador": "Gap vs. Meta",
                "Monto (S/)": f"S/ {res['gap_soles']:,.2f}",
                "Unidades": f"{res['gap_unid']:.0f}",
            },
        ])
        st.dataframe(df_bloque1, use_container_width=True, hide_index=True)

    with col_b1_right:
        st.markdown("**Facturación Acumulada por Horizonte Temporal**")
        fa = res["facturacion_acumulada"]
        df_fact_acum = pd.DataFrame([
            {"Periodo": "Semana actual", "Facturación Bruta (S/)": f"S/ {fa['semana_actual']:,.2f}", "Ventas Netas Activas (S/)": f"S/ {fa['semana_actual']:,.2f}"},
            {"Periodo": "Mes actual", "Facturación Bruta (S/)": f"S/ {fa['mes_actual']:,.2f}", "Ventas Netas Activas (S/)": f"S/ {fa['mes_actual_neta']:,.2f}"},
            {"Periodo": "Trimestre actual", "Facturación Bruta (S/)": f"S/ {fa['trimestre_actual']:,.2f}", "Ventas Netas Activas (S/)": f"S/ {fa['trimestre_actual'] - mix['cancelaciones_soles']:,.2f}"},
            {"Periodo": "Semestre actual", "Facturación Bruta (S/)": f"S/ {fa['semestre_actual']:,.2f}", "Ventas Netas Activas (S/)": f"S/ {fa['semestre_actual'] - mix['cancelaciones_soles']:,.2f}"},
            {"Periodo": "Año actual", "Facturación Bruta (S/)": f"S/ {fa['anio_actual']:,.2f}", "Ventas Netas Activas (S/)": f"S/ {fa['anio_actual_neta']:,.2f}"},
        ])
        st.dataframe(df_fact_acum, use_container_width=True, hide_index=True)
        st.caption("📌 Nota contable: La Facturación Bruta contempla el total de operaciones registradas en el corte; las Ventas Netas Activas descuentan anulaciones o caídas.")

    st.divider()

    # --- BLOQUE 2: MIX CONTADO/FINANCIADO, CASH-IN, PRECIO, DESCUENTOS Y CANCELACIONES ---
    st.subheader("2. Mix Contado / Financiado, Cash-in, Precio, Descuentos y Cancelaciones")
    col_b2_1, col_b2_2 = st.columns([1.3, 1])

    with col_b2_1:
        st.markdown("**Estructura por Tipo de Compra**")
        df_mix_tabla = pd.DataFrame([
            {
                "Tipo": "Contado",
                "Unidades": mix["unid_contado"],
                "% Unid": f"{mix['pct_unid_contado']:.1f}%",
                "Venta S/": f"S/ {mix['venta_contado']:,.2f}",
                "Ticket Promedio": f"S/ {mix['ticket_prom_contado']:,.2f}",
                "% Venta": f"{mix['pct_venta_contado']:.1f}%",
            },
            {
                "Tipo": "Financiado",
                "Unidades": mix["unid_financiado"],
                "% Unid": f"{mix['pct_unid_financiado']:.1f}%",
                "Venta S/": f"S/ {mix['venta_financiado']:,.2f}",
                "Ticket Promedio": f"S/ {mix['ticket_prom_financiado']:,.2f}",
                "% Venta": f"{mix['pct_venta_financiado']:.1f}%",
            },
            {
                "Tipo": "Total",
                "Unidades": res["ventas_reales_unid"],
                "% Unid": "100.0%",
                "Venta S/": f"S/ {res['ventas_reales_soles']:,.2f}",
                "Ticket Promedio": f"S/ {mix['ticket_prom_total']:,.2f}",
                "% Venta": "100.0%",
            },
        ])
        st.dataframe(df_mix_tabla, use_container_width=True, hide_index=True)

        c_m1, c_m2, c_m3 = st.columns(3)
        c_m1.metric("Saldo Financiado Generado", f"S/ {mix['saldo_financiado']:,.2f}", f"{mix['pct_saldo_financiado']:.1f}% de la venta")
        c_m2.metric("Cash-in por Lote Vendido", f"S/ {mix['cash_in_por_lote']:,.2f}")
        c_m3.metric("Inicial Promedio Financiado", f"S/ {mix['inicial_promedio_soles']:,.2f}")

    with col_b2_2:
        st.markdown("**Desglose de Cash-in, Descuentos y Cancelaciones**")
        df_caja_desc = pd.DataFrame([
            {"Concepto": "Iniciales cobradas (Financiado)", "Valor": f"S/ {mix['iniciales_financiado']:,.2f}", "Detalle": f"{mix['iniciales_financiado']/res['ventas_reales_soles']*100:.2f}% de ventas" if res['ventas_reales_soles'] > 0 else "0%"},
            {"Concepto": "Cobros por ventas al Contado", "Valor": f"S/ {mix['cash_in_contado']:,.2f}", "Detalle": f"{mix['cash_in_contado']/res['ventas_reales_soles']*100:.2f}% de ventas" if res['ventas_reales_soles'] > 0 else "0%"},
            {"Concepto": "Cash-in Comercial Total", "Valor": f"S/ {mix['cash_in_total']:,.2f}", "Detalle": f"{cal['cash_in_total_pct']:.2f}% efectividad caja"},
            {"Concepto": "Ventas a Precios de Lista", "Valor": f"S/ {mix['ventas_precio_lista']:,.2f}", "Detalle": f"Protección precio: {mix['proteccion_precio_pct']:.1f}%"},
            {"Concepto": "Descuentos Totales Otorgados", "Valor": f"S/ {mix['descuentos_totales']:,.2f}", "Detalle": f"Prom: S/ {mix['descuento_promedio']:,.2f} / lote"},
            {"Concepto": "Cancelaciones / Ventas Caídas", "Valor": f"S/ {mix['cancelaciones_soles']:,.2f}", "Detalle": f"{mix['cancelaciones_unid']} operación caída"},
            {"Concepto": "Monto Consolidado Bruto", "Valor": f"S/ {mix['monto_consolidado_bruto']:,.2f}", "Detalle": f"{mix['unid_consolidadas_bruto']} operaciones totales"},
        ])
        st.dataframe(df_caja_desc, use_container_width=True, hide_index=True)

    st.divider()

    # --- BLOQUE 3 Y BLOQUE 4: CALIDAD FINANCIERA Y COSTOS/EFICIENCIA ---
    col_b3, col_b4 = st.columns(2)

    with col_b3:
        st.subheader("3. Calidad Financiera de la Venta")
        if cal["indice_calidad_venta"] >= 90:
            st.success(f"**Diagnóstico:** {cal['diagnostico_calidad']} — **Índice: {cal['indice_calidad_venta']:.2f} pts** | **SCORE CSO: {cal['score_cso']:.2f} pts**")
        elif cal["indice_calidad_venta"] >= 80:
            st.warning(f"**Diagnóstico:** {cal['diagnostico_calidad']} — **Índice: {cal['indice_calidad_venta']:.2f} pts** | **SCORE CSO: {cal['score_cso']:.2f} pts**")
        else:
            st.error(f"**Diagnóstico:** {cal['diagnostico_calidad']} — **Índice: {cal['indice_calidad_venta']:.2f} pts** | **SCORE CSO: {cal['score_cso']:.2f} pts**")

        df_calidad = pd.DataFrame([
            {"Indicador de Calidad": "Cash-in total % (Peso 30%)", "Resultado Actual": f"{cal['cash_in_total_pct']:.2f}%", "Parámetro Meta": f"≥ {cfg['Cash_In_Minimo_Pct']*100:.0f}%", "Estado": "🟢" if cal["cash_in_total_pct"] >= cfg["Cash_In_Minimo_Pct"]*100 else "🟡"},
            {"Indicador de Calidad": "Inicial promedio financiado % (Peso 20%)", "Resultado Actual": f"{cal['inicial_promedio_pct']:.2f}%", "Parámetro Meta": f"≥ {cfg['Inicial_Promedio_Min_Pct']*100:.0f}%", "Estado": "🟢" if cal["inicial_promedio_pct"] >= cfg["Inicial_Promedio_Min_Pct"]*100 else "🔴"},
            {"Indicador de Calidad": "Descuentos otorgados % (Peso 20%)", "Resultado Actual": f"{cal['descuentos_pct']:.2f}%", "Parámetro Meta": f"≤ {cfg['Descuento_Maximo_Pct']*100:.0f}%", "Estado": "🟢" if cal["descuentos_pct"] <= cfg["Descuento_Maximo_Pct"]*100 else "🔴"},
            {"Indicador de Calidad": "Cancelación / Caídas % (Peso 20%)", "Resultado Actual": f"{cal['cancelacion_pct']:.2f}%", "Parámetro Meta": f"≤ {cfg['Cancelaciones_Maximo_Pct']*100:.0f}%", "Estado": "🟢" if cal["cancelacion_pct"] <= cfg["Cancelaciones_Maximo_Pct"]*100 else "🟡"},
            {"Indicador de Calidad": "Consolidación de venta % (Peso 10%)", "Resultado Actual": f"{cal['consolidacion_pct']:.2f}%", "Parámetro Meta": f"≥ {cfg['Meta_Consolidacion_Pct']*100:.0f}%", "Estado": "🟢" if cal["consolidacion_pct"] >= cfg["Meta_Consolidacion_Pct"]*100 else "🟡"},
        ])
        st.dataframe(df_calidad, use_container_width=True, hide_index=True)

    with col_b4:
        st.subheader("4. Costos y Eficiencia Comercial (CSO + CMO)")
        c_ef1, c_ef2, c_ef3 = st.columns(3)
        c_ef1.metric("Contribución Comercial", f"S/ {cos['contribucion_comercial']:,.2f}", f"ROI: {cos['roi_comercial']:.2f}x")
        c_ef2.metric("CAC Total por Lote", f"S/ {cos['cac_total']:,.2f}", f"Mkt: S/ {cos['cac_marketing']:,.0f} | Com: S/ {cos['cac_comercial']:,.0f}")
        c_ef3.metric("Venta por S/ 1 Gasto CSO", f"S/ {cos['venta_por_sol_cso']:,.2f}", f"Cash-in/S/1: S/ {cos['cash_in_por_sol_cso']:,.2f}")

        df_costos_res = pd.DataFrame([
            {"Indicador de Eficiencia": "Gastos directos CSO (Comercial)", "Valor": f"S/ {cos['gastos_cso_real']:,.2f}", "% sobre Ventas / Meta": f"{cos['pct_gasto_cso_sobre_venta']:.2f}% de ventas (Presup: S/ {cos['gastos_cso_pres']:,.0f})"},
            {"Indicador de Eficiencia": "Gastos Publicidad y Mkt CMO", "Valor": f"S/ {cos['gastos_cmo_real']:,.2f}", "% sobre Ventas / Meta": f"{cos['pct_gasto_cmo_sobre_venta']:.2f}% de ventas (Presup: S/ {cos['gastos_cmo_pres']:,.0f})"},
            {"Indicador de Eficiencia": "Gastos Comerciales + Mkt Totales", "Valor": f"S/ {cos['gastos_totales']:,.2f}", "% sobre Ventas / Meta": f"Presupuesto consumido: {cos['pct_presupuesto_consumido']:.1f}%"},
            {"Indicador de Eficiencia": "Comisiones sobre Ventas Cerradas", "Valor": "S/ 24,500.00", "% sobre Ventas / Meta": f"{cos['pct_comisiones_ventas']:.2f}% de la venta"},
        ])
        st.dataframe(df_costos_res, use_container_width=True, hide_index=True)

    st.divider()

    # --- BLOQUE 11: QUÉ DEBE RESPONDER EL CSO CADA SEMANA AL CEO ---
    st.subheader("11. Qué debe responder el CSO cada semana (Reporte Ejecutivo al CEO)")
    st.dataframe(dash["preguntas_ceo"], use_container_width=True, hide_index=True)


# ==============================================================================
# PESTAÑA 2: EMBUDO KOMMO, RESUMEN SEMANAL Y EVENTOS (BLOQUES 7, 8, 9 Y 10)
# ==============================================================================
with tab2:
    st.subheader("7. Embudo de Conversiones y Regla Comercial 3:1")

    if "🟢" in emb["alerta_3_1"]:
        st.success(emb["alerta_3_1"])
    elif "🔴" in emb["alerta_3_1"]:
        st.error(emb["alerta_3_1"])
    else:
        st.info(emb["alerta_3_1"])

    col_emb_tabla, col_emb_graf = st.columns([1.3, 1])

    with col_emb_tabla:
        st.markdown("**Tabla de Conversión por Etapa vs. Meta Prorrateada**")
        df_emb_view = emb["df_embudo"].copy()
        df_emb_view["Conversión %"] = df_emb_view["Conversión %"].map(lambda x: f"{x:.2f}%")
        st.dataframe(df_emb_view, use_container_width=True, hide_index=True)

    with col_emb_graf:
        df_etapas_graf = emb["df_embudo"][
            emb["df_embudo"]["Etapa"].isin([
                "Leads", "Respondieron", "Interesados",
                "Agendados al proyecto", "Visitas proyecto", "Separaciones", "Ventas"
            ])
        ]
        fig_funnel = go.Figure(go.Funnel(
            y=df_etapas_graf["Etapa"],
            x=df_etapas_graf["Cantidad"],
            textinfo="value+percent initial",
            marker={"color": ["#1f77b4", "#2b5c8f", "#388e3c", "#f57c00", "#fbc02d", "#7b1fa2", "#2ca02c"]},
        ))
        fig_funnel.update_layout(title="Embudo Comercial Activo (Leads ➔ Cierre)", margin=dict(l=10, r=10, t=40, b=10), height=380)
        st.plotly_chart(fig_funnel, use_container_width=True)

    col_can, col_rsg = st.columns([1, 1.2])
    with col_can:
        st.markdown("**Canales de Captación de Leads**")
        st.dataframe(emb["df_canales"], use_container_width=True, hide_index=True)
    with col_rsg:
        st.markdown("**9. Riesgos de Pipeline y Pérdidas Identificadas**")
        r1, r2, r3 = st.columns(3)
        r1.metric("Cotizaciones >30 días", f"S/ {rsg['pipeline_mas_30_soles']:,.0f}", f"{rsg['pct_pipeline_mas_30']:.1f}% de bolsa")
        r2.metric("Leads sin Respuesta", f"{rsg['perdida_no_respuesta_leads']} leads", "Por re-contactar")
        r3.metric("Caídas / Desistimientos", f"{rsg['oportunidades_perdidas_unid']} lote", f"S/ {rsg['oportunidades_perdidas_soles']:,.0f}")
        st.caption(f"📌 **Causa registrada en caídas:** {rsg['motivo_principal_caida']}")

    st.divider()

    # --- RESUMEN SEMANAL AUTOMÁTICO (PROYECTADA VS REAL) Y BLOQUE 10 ---
    st.subheader("10. Evolución Últimas 12 Semanas y Cobertura Futura")
    col_sem1, col_sem2 = st.columns([1.4, 1])
    with col_sem1:
        st.markdown("**Seguimiento Semanal: Proyectado vs. Real**")
        df_sem_show = emb["df_resumen_semanal"].copy()
        df_sem_show["Facturación Proy. S/"] = df_sem_show["Facturación Proy. S/"].map(lambda x: f"S/ {x:,.0f}")
        df_sem_show["Facturación Real S/"] = df_sem_show["Facturación Real S/"].map(lambda x: f"S/ {x:,.0f}")
        df_sem_show["Cumplimiento %"] = df_sem_show["Cumplimiento %"].map(lambda x: f"{x:.1f}%")
        st.dataframe(df_sem_show, use_container_width=True, hide_index=True, height=320)
    with col_sem2:
        st.markdown("**Planificación y Cobertura por Horizonte**")
        df_plan_show = dash["planificacion"].copy()
        df_plan_show["Meta Venta S/"] = df_plan_show["Meta Venta S/"].map(lambda x: f"S/ {x:,.0f}")
        df_plan_show["Plan / Forecast S/"] = df_plan_show["Plan / Forecast S/"].map(lambda x: f"S/ {x:,.0f}")
        df_plan_show["Cobertura %"] = df_plan_show["Cobertura %"].map(lambda x: f"{x:.1f}%")
        df_plan_show["Presupuesto S/"] = df_plan_show["Presupuesto S/"].map(lambda x: f"S/ {x:,.0f}")
        st.dataframe(df_plan_show, use_container_width=True, hide_index=True)

    st.divider()

    # --- BLOQUE 8: EVENTOS DE CONVERSIÓN ---
    st.subheader("8. Eventos de Conversión — Calendario, Presupuesto, Ventas, Cash-in y ROI")
    ev1, ev2, ev3, ev4, ev5 = st.columns(5)
    ev1.metric("Venta en Eventos", f"S/ {evn['venta_eventos_soles']:,.2f}")
    ev2.metric("Cash-in Eventos", f"S/ {evn['cash_in_eventos_soles']:,.2f}")
    ev3.metric("Costo Real Eventos", f"S/ {evn['costo_eventos_soles']:,.2f}")
    ev4.metric("ROI Eventos", f"{evn['roi_eventos']:.1f}x")
    ev5.metric("Venta por S/ 1 Evento", f"S/ {evn['venta_por_sol_evento']:,.2f}")

    st.dataframe(evn["df_eventos"], use_container_width=True, hide_index=True, height=320)


# ==============================================================================
# PESTAÑA 3: PRODUCTIVIDAD DE ASESORES E INVENTARIO (BLOQUES 5 Y 6)
# ==============================================================================
with tab3:
    st.subheader("6. Productividad y Ranking por Asesor Comercial")

    a1, a2, a3, a4, a5, a6 = st.columns(6)
    a1.metric("Asesores Activos", f"{eqp['asesores_activos']} vendedores")
    a2.metric("Capacidad Mensual", f"{eqp['capacidad_leads_mes']:.0f} leads/mes")
    a3.metric("Leads Asignados", f"{eqp['leads_asignados']} prospectos")
    a4.metric("Uso de Capacidad", f"{eqp['uso_capacidad_pct']:.1f}%")
    a5.metric("Calidad Promedio", f"{eqp['calidad_promedio_asesores']:.1f} pts")
    a6.metric("Venta por Lead Global", f"S/ {eqp['venta_por_lead_soles']:,.2f}")

    df_as_view = eqp["df_asesores"].copy()
    if not df_as_view.empty:
        col_top_v, col_graf_v = st.columns([1, 1.3])
        with col_top_v:
            st.markdown("**🏆 Top 3 Vendedores del Periodo (Cierre en S/)**")
            df_top3 = df_as_view.head(3)[["Ranking", "Vendedor", "Leads", "Ventas Cant", "Venta S/.", "Cash-in S/.", "Score Comercial"]].copy()
            df_top3["Venta S/."] = df_top3["Venta S/."].map(lambda x: f"S/ {x:,.2f}")
            df_top3["Cash-in S/."] = df_top3["Cash-in S/."].map(lambda x: f"S/ {x:,.2f}")
            df_top3["Score Comercial"] = df_top3["Score Comercial"].map(lambda x: f"{x:.2f} pts")
            st.dataframe(df_top3, use_container_width=True, hide_index=True)

        with col_graf_v:
            fig_as = px.bar(
                df_as_view,
                x="Vendedor",
                y="Leads",
                color="Venta S/.",
                text_auto=True,
                title="Distribución de Leads Asignados vs. Facturación Cerrada por Asesor",
                color_continuous_scale="Tealgrn",
            )
            fig_as.update_layout(height=300, margin=dict(l=10, r=10, t=40, b=10))
            st.plotly_chart(fig_as, use_container_width=True)

        st.markdown("**Matriz Completa de Resultados por Vendedor**")
        cols_orden = [
            "Ranking", "Vendedor", "Lider", "Estado", "Leads", "Respondieron",
            "Agendados", "Visitas", "Separaciones", "Ventas Cant", "Venta S/.",
            "% Meta Venta", "Conv. Lead→Venta %", "Venta/Lead S/", "Ticket Promedio S/",
            "Cash-in S/.", "Cash-in %", "Calidad Vendedor", "Diagnóstico Calidad", "Score Comercial"
        ]
        st.dataframe(
            df_as_view[[c for c in cols_orden if c in df_as_view.columns]],
            use_container_width=True,
            hide_index=True,
        )

    st.divider()

    # --- BLOQUE 5: INVENTARIO, ABSORCIÓN, AGING Y PRICING ---
    st.subheader("5. Inventario Comercial — Absorción, Aging (>90 días) y Pricing")

    i1, i2, i3, i4, i5, i6 = st.columns(6)
    i1.metric("Inventario Total", f"{inv['inventario_total']} lotes", "100% proyecto")
    i2.metric("Total Vendidos", f"{inv['total_vendidos']} lotes", f"{inv['pct_vendidos']:.2f}% vendido")
    i3.metric("Falta por Vender", f"{inv['falta_vender']} lotes", f"{inv['pct_falta_vender']:.2f}% stock")
    i4.metric("Velocidad / Absorción", f"{inv['velocidad_mensual']:.2f} lotes/mes", f"{inv['absorcion_mensual_pct']:.2f}% stock/mes")
    i5.metric("Meses de Inventario", f"{inv['meses_inventario']:.1f} meses", f"{inv['lotes_mas_90_dias']} lotes >90d")
    i6.metric("Próximo Aumento Precio", f"Faltan {inv['lotes_para_aumento_precio']} lotes", f"{inv['unidades_sin_visitas']} lotes con 0 visitas")

    if not df_inventario.empty:
        col_fil_i1, col_fil_i2, col_fil_i3 = st.columns(3)
        with col_fil_i1:
            etapas_inv = ["Todas"] + sorted(df_inventario["Etapa"].dropna().astype(str).unique().tolist())
            etapa_sel = st.selectbox("Filtrar por Etapa", etapas_inv)
        with col_fil_i2:
            estados_inv = ["Todos"] + sorted(df_inventario["Estado"].dropna().astype(str).unique().tolist())
            estado_sel = st.selectbox("Filtrar por Estado del Lote", estados_inv)
        with col_fil_i3:
            demandas_inv = ["Todas"] + sorted(df_inventario["Demanda"].dropna().astype(str).unique().tolist())
            demanda_sel = st.selectbox("Filtrar por Nivel de Demanda", demandas_inv)

        df_inv_filtrado = df_inventario.copy()
        if etapa_sel != "Todas":
            df_inv_filtrado = df_inv_filtrado[df_inv_filtrado["Etapa"] == etapa_sel]
        if estado_sel != "Todos":
            df_inv_filtrado = df_inv_filtrado[df_inv_filtrado["Estado"] == estado_sel]
        if demanda_sel != "Todas":
            df_inv_filtrado = df_inv_filtrado[df_inv_filtrado["Demanda"] == demanda_sel]

        st.dataframe(df_inv_filtrado, use_container_width=True, hide_index=True, height=350)


# ==============================================================================
# PESTAÑA 4: GESTIÓN DE DATOS EN VIVO (CRUD) DESDE LA INTERFAZ
# ==============================================================================
with tab4:
    st.subheader("📝 Gestión y Actualización de Datos en Vivo (CRUD)")
    st.markdown(
        "Agrega nuevos registros, modifica celdas directamente o elimina filas seleccionándolas "
        "y presionando `Supr`. Al guardar, **todos los indicadores, embudos y gráficos del sistema se recalculan al instante**."
    )

    tabla_editar = st.selectbox(
        "📂 Selecciona el módulo de datos que deseas actualizar:",
        [
            "1. Operaciones de Venta y Cierres (Data_Ventas)",
            "2. Cotizaciones y Separaciones en Curso (Data_Cotiz)",
            "3. Prospectos y Seguimiento CRM (Data_Leads)",
            "4. Plan Mensual de Metas y Presupuestos (Meta)",
            "5. Plantilla de Asesores Comerciales (Asesores)",
            "6. Gastos Comerciales CSO y CMO (Costos)",
            "7. Calendario y Resultados de Eventos (Eventos)",
            "8. Maestro de Inventario de Lotes (Inventario)",
            "9. Parámetros y Reglas de Negocio (Configuración)",
        ],
    )

    if tabla_editar.startswith("1."):
        st.caption("💡 Los descuentos (`Dscto S/.`, `Dscto %`), el `Saldo` financiado y los `Dias cierre` se calculan automáticamente al guardar.")
        df_ed = st.data_editor(
            df_ventas,
            num_rows="dynamic",
            use_container_width=True,
            key="ed_cso_ventas",
            column_config={
                "Vendedor": st.column_config.SelectboxColumn("Vendedor", options=LISTA_VENDEDORES, required=True),
                "Fuente": st.column_config.SelectboxColumn("Fuente", options=LISTA_FUENTES),
                "Estado_CRM": st.column_config.SelectboxColumn("Estado Operación", options=LISTA_ESTADOS_VENTA, required=True),
                "Tipo de Venta": st.column_config.SelectboxColumn("Modalidad", options=["Financiado", "Contado"], required=True),
                "Precio Lista": st.column_config.NumberColumn("Precio Lista (S/)", min_value=0.0, format="S/ %.2f"),
                "Precio venta": st.column_config.NumberColumn("Precio Venta (S/)", min_value=0.0, format="S/ %.2f"),
                "Inicial": st.column_config.NumberColumn("Inicial Pagada (S/)", min_value=0.0, format="S/ %.2f"),
            },
        )
        if st.button("💾 Guardar Cambios en Ventas", type="primary"):
            data_manager.guardar_cso_ventas(df_ed)
            st.success("✅ Operaciones de venta actualizadas correctamente.")
            st.rerun()

    elif tabla_editar.startswith("2."):
        df_ed = st.data_editor(
            df_cotiz,
            num_rows="dynamic",
            use_container_width=True,
            key="ed_cso_cotiz",
            column_config={
                "Vendedor": st.column_config.SelectboxColumn("Vendedor", options=LISTA_VENDEDORES),
                "Fuente": st.column_config.SelectboxColumn("Fuente", options=LISTA_FUENTES),
                "Estado_CRM": st.column_config.SelectboxColumn("Estado", options=["Listo para Comprar", "Separado", "En Cotizacion"]),
                "Precio Lista": st.column_config.NumberColumn("Precio Lista (S/)", min_value=0.0, format="S/ %.2f"),
                "Precio venta": st.column_config.NumberColumn("Precio Cotizado (S/)", min_value=0.0, format="S/ %.2f"),
            },
        )
        if st.button("💾 Guardar Cambios en Cotizaciones", type="primary"):
            data_manager.guardar_cso_cotiz(df_ed)
            st.success("✅ Cotizaciones y separaciones actualizadas.")
            st.rerun()

    elif tabla_editar.startswith("3."):
        df_ed = st.data_editor(
            df_leads,
            num_rows="dynamic",
            use_container_width=True,
            key="ed_cso_leads",
            column_config={
                "Vendedor": st.column_config.SelectboxColumn("Vendedor Asignado", options=LISTA_VENDEDORES),
                "Estado_CRM": st.column_config.SelectboxColumn("Estado CRM", options=LISTA_ESTADOS_KOMMO),
                "Fuente": st.column_config.SelectboxColumn("Fuente", options=LISTA_FUENTES),
                "Monto_Cotizado": st.column_config.NumberColumn("Monto Cotizado (S/)", min_value=0.0, format="S/ %.2f"),
            },
        )
        if st.button("💾 Guardar Cambios en Prospectos CRM", type="primary"):
            data_manager.guardar_cso_leads(df_ed)
            st.success("✅ Base de prospectos actualizada y homologada.")
            st.rerun()

    elif tabla_editar.startswith("4."):
        st.caption("💡 Edita las metas mensuales base; las columnas de Forecast, Venta Real y Metas de Embudo se recalculan automáticamente.")
        df_ed = st.data_editor(df_meta, num_rows="dynamic", use_container_width=True, key="ed_cso_meta")
        if st.button("💾 Guardar Cambios en Metas Mensuales", type="primary"):
            data_manager.guardar_cso_meta(df_ed)
            st.success("✅ Plan mensual de metas actualizado.")
            st.rerun()
        st.markdown("**Vista Calculada Completa del Plan Mensual (con Forecast y Embudo Proyectado):**")
        st.dataframe(dash["df_meta_enriquecida"], use_container_width=True, hide_index=True)

    elif tabla_editar.startswith("5."):
        df_ed = st.data_editor(
            df_asesores,
            num_rows="dynamic",
            use_container_width=True,
            key="ed_cso_asesores",
            column_config={
                "Estado": st.column_config.SelectboxColumn("Estado", options=["Activo", "No activo"], required=True),
                "Meta Unid Mensual": st.column_config.NumberColumn("Meta Lotes / Mes", min_value=0.0, step=1.0),
            },
        )
        if st.button("💾 Guardar Cambios en Plantilla de Asesores", type="primary"):
            data_manager.guardar_cso_asesores(df_ed)
            st.success("✅ Plantilla de asesores actualizada.")
            st.rerun()

    elif tabla_editar.startswith("6."):
        df_ed = st.data_editor(
            df_costos,
            num_rows="dynamic",
            use_container_width=True,
            key="ed_cso_costos",
            column_config={
                "Área": st.column_config.SelectboxColumn("Área", options=["CSO", "CMO"], required=True),
                "Presupuesto": st.column_config.NumberColumn("Presupuesto (S/)", min_value=0.0, format="S/ %.2f"),
                "Real": st.column_config.NumberColumn("Ejecutado Real (S/)", min_value=0.0, format="S/ %.2f"),
            },
        )
        if st.button("💾 Guardar Cambios en Gastos Comerciales", type="primary"):
            data_manager.guardar_cso_costos(df_ed)
            st.success("✅ Presupuesto y ejecución de gastos actualizados.")
            st.rerun()

    elif tabla_editar.startswith("7."):
        df_ed = st.data_editor(df_eventos, num_rows="dynamic", use_container_width=True, key="ed_cso_eventos")
        if st.button("💾 Guardar Cambios en Eventos", type="primary"):
            data_manager.guardar_cso_eventos(df_ed)
            st.success("✅ Calendario de eventos actualizado.")
            st.rerun()

    elif tabla_editar.startswith("8."):
        df_ed = st.data_editor(
            df_inventario,
            num_rows="dynamic",
            use_container_width=True,
            key="ed_cso_inv",
            column_config={
                "Estado": st.column_config.SelectboxColumn("Estado", options=["Disponible", "Vendido", "Separado"]),
                "Demanda": st.column_config.SelectboxColumn("Demanda", options=["Alta", "Media", "Baja"]),
                "Precio lista": st.column_config.NumberColumn("Precio Lista (S/)", min_value=0.0, format="S/ %.2f"),
                "Precio actual": st.column_config.NumberColumn("Precio Actual (S/)", min_value=0.0, format="S/ %.2f"),
            },
        )
        if st.button("💾 Guardar Cambios en Inventario", type="primary"):
            data_manager.guardar_cso_inventario(df_ed)
            st.success("✅ Inventario de lotes actualizado.")
            st.rerun()

    elif tabla_editar.startswith("9."):
        df_cfg_raw = data_manager.cargar_cso_config_df()
        df_ed = st.data_editor(df_cfg_raw, num_rows="dynamic", use_container_width=True, key="ed_cso_cfg")
        if st.button("💾 Guardar Parámetros de Configuración", type="primary"):
            data_manager.guardar_cso_config_df(df_ed)
            st.success("✅ Parámetros comerciales actualizados.")
            st.rerun()

    st.divider()

    # Importador masivo dejado abajo en un bloque desplegable opcional y con texto 100% corporativo
    with st.expander("📥 Carga Masiva / Sincronización desde Archivo Excel (.xlsx) — Opcional"):
        st.markdown(
            "Utiliza esta herramienta únicamente cuando desees importar un corte masivo desde una plantilla Excel externa. "
            "Para la operación diaria, edita los registros directamente en la tabla interactiva superior."
        )
        col_up1, col_up2 = st.columns([2, 1])
        with col_up1:
            archivo_subido = st.file_uploader(
                "Seleccionar archivo Excel Comercial (.xlsx)",
                type=["xlsx"],
                key="uploader_excel_cso",
            )
        with col_up2:
            st.write("")
            st.write("")
            if st.button("🔄 Importar y Sincronizar Tablas", use_container_width=True):
                if archivo_subido is not None:
                    res_imp = data_manager.importar_excel_comercial(archivo_subido)
                    if res_imp.get("ok"):
                        st.success(f"✅ {res_imp['mensaje']} Detalle: {res_imp.get('resumen')}")
                        st.rerun()
                    else:
                        st.error(res_imp.get("mensaje"))
                else:
                    res_local = data_manager.importar_excel_comercial()
                    if res_local.get("ok"):
                        st.success(f"✅ Sincronizado con éxito: {res_local.get('resumen')}")
                        st.rerun()
                    else:
                        st.warning("Selecciona un archivo .xlsx para realizar la importación.")
