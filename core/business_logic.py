import pandas as pd

def calcular_resumen_gerencial(df_mkt, df_ventas, df_finanzas):
    # 1. Marketing
    total_mkt = df_mkt["Presupuesto"].sum() if not df_mkt.empty else 0.0
    total_leads = df_mkt["Leads"].sum() if not df_mkt.empty else 0

    # 2. Ventas
    if not df_ventas.empty:
        descuentos = df_ventas["Venta_Bruta"] * (df_ventas["Descuento_Pct"] / 100)
        ventas_netas = (df_ventas["Venta_Bruta"] - descuentos).sum()
        total_unidades = len(df_ventas)
    else:
        ventas_netas = 0.0
        total_unidades = 0

    # 3. Finanzas
    gastos_operativos = df_finanzas["Monto"].sum() if not df_finanzas.empty else 0.0

    # 4. Indicadores Financieros
    egresos_totales = gastos_operativos + total_mkt
    utilidad_operativa = ventas_netas - egresos_totales
    margen_operativo = (utilidad_operativa / ventas_netas * 100) if ventas_netas > 0 else 0.0

    # 5. Métricas Cruzadas (Eficiencia Comercial)
    # Tasa de conversión: Inmuebles vendidos vs Leads captados
    conversion_leads_pct = (total_unidades / total_leads * 100) if total_leads > 0 else 0.0
    # Costo publicitario por unidad vendida
    cac_unidad = (total_mkt / total_unidades) if total_unidades > 0 else 0.0

    return {
        "ventas_netas": ventas_netas,
        "egresos_totales": egresos_totales,
        "gastos_operativos": gastos_operativos,
        "inversion_mkt": total_mkt,
        "utilidad_operativa": utilidad_operativa,
        "margen_operativo": margen_operativo,
        "total_unidades": total_unidades,
        "total_leads": total_leads,
        "conversion_leads_pct": conversion_leads_pct,
        "cac_unidad": cac_unidad
    }