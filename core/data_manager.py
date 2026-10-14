import os
import pandas as pd
import numpy as np

# Directorio raíz de almacenamiento local (carpeta data/ en la raíz del proyecto)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

# Nombre por defecto del archivo maestro de Excel si se coloca en data/ o en la raíz
DEFAULT_EXCEL_NAMES = [
    "Dashboard Reporte Comercial.xlsx",
    "dashboard_reporte_comercial.xlsx",
    "Reporte Comercial.xlsx",
]

# ==============================================================================
# 1. DICCIONARIOS DE HOMOLOGACIÓN Y LIMPIEZA (ETL KOMMO CRM -> DASHBOARD CSO)
# ==============================================================================

# Unifica las variantes de nombres de asesores que vienen de Kommo CRM (Data_Leads)
# con los nombres oficiales de la tabla Asesores y Data_Ventas
MAPA_VENDEDORES = {
    "jhovana valdez": "Jhovana",
    "jhovana": "Jhovana",
    "jose carrillo rios": "Jose Carrillo",
    "jose carrillo": "Jose Carrillo",
    "josue vicente": "Josue",
    "josue": "Josue",
    "alfredo caceda": "Alfredo Caceda",
    "ingrid villegas": "Ingrid Villegas",
    "vicente quispe": "Vicente Quispe",
    "jeanpaul campos": "JeanPaul Campos",
    "juan carlos paredes": "Juan Carlos Paredes",
    "karina": "Karina",
    "herberth": "Herberth",
    "jose cornejo": "Jose Cornejo",
    "eduardo campos alvarado": "Eduardo Campos",
}

# Clasifica cualquier texto de Estado_CRM de Kommo en una etapa estándar del embudo
MAPA_ETAPA_EMBUDO = {
    "no contesta - por confirmar": "No respondieron",
    "no contesta 3v": "No respondieron",
    "realizar invitacion": "No respondieron",
    "realizar invitación": "No respondieron",
    "respondieron llamada/ whatsapp": "Respondieron",
    "respondieron": "Respondieron",
    "seguimiento": "Respondieron",
    "interesado": "Interesados",
    "interesados": "Interesados",
    "en cotizacion": "Interesados",
    "en cotización": "Interesados",
    "listo para comprar": "Listo para Comprar",
    "agendo oficina /presentación virtual": "Asistió Zoom",
    "agendo oficina /presentacion virtual": "Asistió Zoom",
    "presentación zoom": "Asistió Zoom",
    "presentacion zoom": "Asistió Zoom",
    "agendo visita al proyecto": "Agendados al proyecto",
    "no asistio": "No asistió al proyecto",
    "no asistió": "No asistió al proyecto",
    "asistio al proyecto": "Visitas proyecto",
    "asistió al proyecto": "Visitas proyecto",
    "visitó proyecto": "Visitas proyecto",
    "visito proyecto": "Visitas proyecto",
    "separado": "Separaciones",
    "separo lote": "Separaciones",
    "venta": "Ventas",
    "lote vendido": "Ventas",
    "venta perdida": "Desistió (devolución)",
}


def normalizar_vendedor(nombre) -> str:
    """Homologa el nombre del asesor para que crucen leads, cotizaciones y ventas."""
    if pd.isna(nombre) or str(nombre).strip() == "" or str(nombre).strip() == "0":
        return "Sin asignar"
    limpio = str(nombre).strip()
    clave = limpio.lower()
    return MAPA_VENDEDORES.get(clave, limpio.title())


def normalizar_etapa_crm(estado) -> str:
    """Convierte el estado crudo de Kommo CRM en la etapa oficial del embudo."""
    if pd.isna(estado) or str(estado).strip() == "" or str(estado).strip() == "0":
        return "Sin estado"
    limpio = str(estado).strip()
    clave = limpio.lower()
    return MAPA_ETAPA_EMBUDO.get(clave, limpio)


# ==============================================================================
# 2. MOTOR ETL: IMPORTADOR Y LIMPIADOR AUTOMÁTICO DESDE EXCEL (.XLSX)
# ==============================================================================

def _encontrar_excel_local():
    """Busca si el archivo Excel maestro está en data/ o en la raíz del proyecto."""
    for folder in [DATA_DIR, BASE_DIR]:
        if not os.path.exists(folder):
            continue
        for fname in DEFAULT_EXCEL_NAMES:
            candidate = os.path.join(folder, fname)
            if os.path.exists(candidate):
                return candidate
        for fname in os.listdir(folder):
            if fname.lower().endswith(".xlsx") and not fname.startswith("~$"):
                return os.path.join(folder, fname)
    return None


def importar_excel_comercial(origen_excel=None) -> dict:
    """
    Lee el archivo Excel del CSO (desde ruta local o archivo subido en Streamlit),
    limpia filas basura, evalúa/normaliza columnas y guarda las tablas limpias en data/.
    """
    if origen_excel is None:
        origen_excel = _encontrar_excel_local()
    if origen_excel is None:
        return {"ok": False, "mensaje": "No se encontró un archivo Excel para importar."}

    try:
        xls = pd.ExcelFile(origen_excel)
        resumen = {}

        # 1. DATA_VENTAS (Limpiar las ~1,000 filas fantasma con ceros)
        if "Data_Ventas" in xls.sheet_names:
            df_v = pd.read_excel(xls, sheet_name="Data_Ventas")
            df_v = df_v.dropna(how="all")
            # Filtrar filas donde Vendedor, Cliente y Estado_CRM no sean nulos ni ceros vacíos
            mask_valido = (
                df_v["Estado_CRM"].notna()
                & (df_v["Estado_CRM"].astype(str).str.strip() != "0")
                & (df_v["Estado_CRM"].astype(str).str.strip() != "")
            )
            df_v = df_v[mask_valido].copy()
            df_v["Fecha_Lead"] = pd.to_datetime(df_v["Fecha_Lead"], errors="coerce")
            df_v["Fecha firma"] = pd.to_datetime(df_v["Fecha firma"], errors="coerce")
            df_v["Vendedor_Original"] = df_v["Vendedor"]
            df_v["Vendedor"] = df_v["Vendedor"].apply(normalizar_vendedor)
            df_v["Etapa_Embudo"] = df_v["Estado_CRM"].apply(normalizar_etapa_crm)

            for col_num in ["Monto_Separacion", "Precio Lista", "Precio venta", "Dscto S/.", "Dscto %", "Inicial", "Saldo"]:
                if col_num in df_v.columns:
                    df_v[col_num] = pd.to_numeric(df_v[col_num], errors="coerce").fillna(0.0)

            # Recalcular columnas de fórmulas de Excel por seguridad
            df_v["Dscto S/."] = (df_v["Precio Lista"] - df_v["Precio venta"]).clip(lower=0.0)
            df_v["Dscto %"] = np.where(df_v["Precio Lista"] > 0, df_v["Dscto S/."] / df_v["Precio Lista"], 0.0)
            df_v["Saldo"] = (df_v["Precio venta"] - df_v["Inicial"]).clip(lower=0.0)
            dias = (df_v["Fecha firma"] - df_v["Fecha_Lead"]).dt.days
            df_v["Dias cierre"] = dias.fillna(0).clip(lower=0).astype(int)

            df_v.to_csv(os.path.join(DATA_DIR, "cso_ventas.csv"), index=False)
            resumen["ventas"] = len(df_v)

        # 2. DATA_COTIZ (Limpiar filas vacías de cotizaciones/separaciones)
        if "Data_Cotiz" in xls.sheet_names:
            df_c = pd.read_excel(xls, sheet_name="Data_Cotiz")
            df_c = df_c.dropna(how="all")
            mask_c = (
                df_c["Estado_CRM"].notna()
                & (df_c["Estado_CRM"].astype(str).str.strip() != "0")
                & (df_c["Estado_CRM"].astype(str).str.strip() != "")
            )
            df_c = df_c[mask_c].copy()
            df_c["Fecha_Lead"] = pd.to_datetime(df_c["Fecha_Lead"], errors="coerce")
            df_c["Vendedor"] = df_c["Vendedor"].apply(normalizar_vendedor)
            df_c["Etapa_Embudo"] = df_c["Estado_CRM"].apply(normalizar_etapa_crm)
            for col_num in ["Monto_Separacion", "Precio Lista", "Precio venta", "Dscto S/.", "Dscto %", "Inicial", "Saldo"]:
                if col_num in df_c.columns:
                    df_c[col_num] = pd.to_numeric(df_c[col_num], errors="coerce").fillna(0.0)
            df_c.to_csv(os.path.join(DATA_DIR, "cso_cotiz.csv"), index=False)
            resumen["cotizaciones"] = len(df_c)

        # 3. DATA_LEADS (Kommo CRM: 597 prospectos con homologación de vendedor y estado)
        if "Data_Leads" in xls.sheet_names:
            df_l = pd.read_excel(xls, sheet_name="Data_Leads")
            df_l = df_l.dropna(how="all", subset=["Fecha_Lead", "Cliente", "Vendedor", "Estado_CRM"]).copy()
            df_l["Fecha_Lead"] = pd.to_datetime(df_l["Fecha_Lead"], errors="coerce")
            df_l["Vendedor_Kommo"] = df_l["Vendedor"]
            df_l["Vendedor"] = df_l["Vendedor"].apply(normalizar_vendedor)
            df_l["Etapa_Embudo"] = df_l["Estado_CRM"].apply(normalizar_etapa_crm)
            df_l["Monto_Cotizado"] = pd.to_numeric(df_l.get("Monto_Cotizado", 0.0), errors="coerce").fillna(0.0)
            df_l["Fuente"] = df_l["Fuente"].fillna("Publicidad pagada").astype(str).str.strip()
            df_l["Proyecto"] = df_l["Proyecto"].fillna("Paraiso de Santa Maria").astype(str).str.strip()
            df_l.to_csv(os.path.join(DATA_DIR, "cso_leads.csv"), index=False)
            resumen["leads"] = len(df_l)

        # 4. META (Saltar las 3 primeras filas decorativas; encabezado real en fila 4 -> header=3)
        if "Meta" in xls.sheet_names:
            df_m = pd.read_excel(xls, sheet_name="Meta", header=3)
            df_m = df_m.dropna(how="all")
            df_m = df_m[df_m["Mes"].notna()].copy()
            df_m["Mes"] = pd.to_datetime(df_m["Mes"], errors="coerce")
            df_m = df_m[df_m["Mes"].notna()].copy()
            cols_meta = ["Meta venta S/", "Meta lotes", "Meta cash-in S/", "Presupuesto CSO", "Presupuesto CMO", "Eventos plan"]
            for c in cols_meta:
                if c in df_m.columns:
                    df_m[c] = pd.to_numeric(df_m[c], errors="coerce").fillna(0.0)
            # Guardar columnas base de metas
            df_m_clean = df_m[["Mes"] + [c for c in cols_meta if c in df_m.columns]].copy()
            df_m_clean.to_csv(os.path.join(DATA_DIR, "cso_meta.csv"), index=False)
            resumen["meses_meta"] = len(df_m_clean)

        # 5. ASESORES (Plantilla de asesores; encabezado en fila 4 -> header=3)
        if "Asesores" in xls.sheet_names:
            df_a = pd.read_excel(xls, sheet_name="Asesores", header=3)
            df_a = df_a[df_a["Vendedor"].notna()].copy()
            df_a["Vendedor"] = df_a["Vendedor"].apply(normalizar_vendedor)
            df_a["Lider"] = df_a["Lider"].fillna("").astype(str).str.strip()
            df_a["Estado"] = df_a["Estado"].fillna("Activo").astype(str).str.strip()
            df_a["Meta Unid Mensual"] = pd.to_numeric(df_a.get("Meta Unid Mensual", 3.0), errors="coerce").fillna(3.0)
            df_a_clean = df_a[["Vendedor", "Lider", "Estado", "Fecha ingreso", "Meta Unid Mensual"]].drop_duplicates(subset=["Vendedor"]).copy()
            df_a_clean.to_csv(os.path.join(DATA_DIR, "cso_asesores.csv"), index=False)
            resumen["asesores"] = len(df_a_clean)

        # 6. COSTOS (Gastos CSO y CMO; encabezado en fila 4 -> header=3)
        if "Costos" in xls.sheet_names:
            df_g = pd.read_excel(xls, sheet_name="Costos", header=3)
            df_g = df_g[df_g["Gasto_ID"].notna()].copy()
            df_g["Fecha"] = pd.to_datetime(df_g["Fecha"], errors="coerce")
            df_g["Presupuesto"] = pd.to_numeric(df_g["Presupuesto"], errors="coerce").fillna(0.0)
            df_g["Real"] = pd.to_numeric(df_g["Real"], errors="coerce").fillna(0.0)
            df_g["Variación S/"] = df_g["Real"] - df_g["Presupuesto"]
            df_g["Variación %"] = np.where(df_g["Presupuesto"] > 0, df_g["Variación S/"] / df_g["Presupuesto"], 0.0)
            cols_g = ["Gasto_ID", "Fecha", "Área", "Categoría", "Detalle / Evento", "Presupuesto", "Real", "Variación S/", "Variación %", "Responsable"]
            df_g = df_g[[c for c in cols_g if c in df_g.columns]].copy()
            df_g.to_csv(os.path.join(DATA_DIR, "cso_costos.csv"), index=False)
            resumen["costos"] = len(df_g)

        # 7. EVENTOS (Calendario de eventos; encabezado en fila 3 -> header=2)
        if "eventos" in xls.sheet_names:
            df_e = pd.read_excel(xls, sheet_name="eventos", header=2)
            df_e = df_e[df_e["Evento_ID"].notna()].copy()
            df_e["Fecha"] = pd.to_datetime(df_e["Fecha"], errors="coerce")
            num_cols_ev = [
                "Meta registrados", "Registrados real", "Meta asistentes", "Asistentes real",
                "Conversión meta", "Ventas unid. real", "Ticket esperado", "Venta real S/",
                "Presupuesto", "Costo real", "Cash-in proyectado", "Cash-in real"
            ]
            for c in num_cols_ev:
                if c in df_e.columns:
                    df_e[c] = pd.to_numeric(df_e[c], errors="coerce").fillna(0.0)
            cols_ev_keep = ["Evento_ID", "Fecha", "Evento", "Tipo", "Proyecto"] + [c for c in num_cols_ev if c in df_e.columns]
            df_e = df_e[cols_ev_keep].copy()
            df_e.to_csv(os.path.join(DATA_DIR, "cso_eventos.csv"), index=False)
            resumen["eventos"] = len(df_e)

        # 8. INVENTARIO (181 lotes; encabezado en fila 3 -> header=2)
        if "Inventario" in xls.sheet_names:
            df_i = pd.read_excel(xls, sheet_name="Inventario", header=2)
            df_i = df_i[df_i["Lote"].notna()].copy()
            df_i["Fecha liberación"] = pd.to_datetime(df_i["Fecha liberación"], errors="coerce")
            df_i["Fecha venta"] = pd.to_datetime(df_i["Fecha venta"], errors="coerce")
            for c in ["m2", "Precio lista", "Precio actual", "N° visitas", "N° cotizaciones", "Próximo precio"]:
                if c in df_i.columns:
                    df_i[c] = pd.to_numeric(df_i[c], errors="coerce").fillna(0.0)
            cols_inv = [
                "Lote", "Manzana", "Etapa", "m2", "Precio lista", "Precio actual",
                "Estado", "Fecha liberación", "Fecha venta", "Días disponible",
                "Aging", "N° visitas", "N° cotizaciones", "Demanda", "Próximo precio", "Trigger precio"
            ]
            df_i = df_i[[c for c in cols_inv if c in df_i.columns]].copy()
            df_i.to_csv(os.path.join(DATA_DIR, "cso_inventario.csv"), index=False)
            resumen["inventario"] = len(df_i)

        # 9. CONFIGURACION (Parámetros y metas de calidad del CSO)
        df_cfg = pd.DataFrame([
            {"Parametro": "Inicio_Venta", "Valor": "2025-10-01", "Descripcion": "Fecha de inicio de comercialización del proyecto"},
            {"Parametro": "Conv_Lead_Agendado", "Valor": "0.20", "Descripcion": "Meta conversión Lead a Agendado (20%)"},
            {"Parametro": "Asistencia_Agendado_Visita", "Valor": "0.60", "Descripcion": "Meta asistencia Agendado a Visita (60%)"},
            {"Parametro": "Conv_Visita_Separacion", "Valor": "0.333333", "Descripcion": "Regla comercial 3:1 (33.3% Visita a Separación)"},
            {"Parametro": "Conv_Separacion_Venta", "Valor": "0.80", "Descripcion": "Meta conversión Separación a Venta (80%)"},
            {"Parametro": "Ticket_Promedio_Meta", "Valor": "40000.0", "Descripcion": "Ticket promedio de venta referencial (S/)"},
            {"Parametro": "Meta_Ventas_Mensual_Unid", "Valor": "10.0", "Descripcion": "Meta de unidades vendidas por mes"},
            {"Parametro": "Semanas_Operativas_Mes", "Valor": "4.33", "Descripcion": "Semanas operativas promedio por mes"},
            {"Parametro": "Cash_In_Minimo_Pct", "Valor": "0.35", "Descripcion": "Cash-in mínimo esperado sobre ventas (35%)"},
            {"Parametro": "Inicial_Promedio_Min_Pct", "Valor": "0.20", "Descripcion": "Inicial promedio mínima en ventas financiadas (20%)"},
            {"Parametro": "Descuento_Maximo_Pct", "Valor": "0.04", "Descripcion": "Descuento máximo permitido sobre lista (4%)"},
            {"Parametro": "Cancelaciones_Maximo_Pct", "Valor": "0.05", "Descripcion": "Tasa máxima tolerada de caídas/cancelaciones (5%)"},
            {"Parametro": "Meta_Consolidacion_Pct", "Valor": "0.95", "Descripcion": "Meta de ventas consolidadas vs brutas (95%)"},
            {"Parametro": "Capacidad_Leads_Mes_Asesor", "Valor": "80.0", "Descripcion": "Capacidad mensual de atención de leads por asesor activo"},
        ])
        df_cfg.to_csv(os.path.join(DATA_DIR, "cso_config.csv"), index=False)

        return {"ok": True, "mensaje": "Excel comercial importado y depurado con éxito.", "resumen": resumen}

    except Exception as e:
        return {"ok": False, "mensaje": f"Error al importar el archivo Excel: {e}"}


def asegurar_datos_cso():
    """
    Verifica si ya existen los archivos CSV limpios del CSO en data/.
    Si no existen y hay un archivo Excel en data/ o en la raíz, lo importa automáticamente.
    """
    archivo_clave = os.path.join(DATA_DIR, "cso_ventas.csv")
    if not os.path.exists(archivo_clave):
        excel_local = _encontrar_excel_local()
        if excel_local:
            importar_excel_comercial(excel_local)


# ==============================================================================
# 3. FUNCIONES DE CARGA Y GUARDADO DEL MÓDULO CSO (VENTAS AVANZADO)
# ==============================================================================

def _cargar_csv_seguro(nombre_archivo, columnas_base, parse_dates=None):
    asegurar_datos_cso()
    path = os.path.join(DATA_DIR, nombre_archivo)
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        df = pd.DataFrame(columns=columnas_base)
        df.to_csv(path, index=False)
        return df
    try:
        df = pd.read_csv(path)
        if parse_dates:
            for col in parse_dates:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors="coerce")
        return df
    except Exception:
        return pd.DataFrame(columns=columnas_base)


def cargar_cso_ventas():
    cols = [
        "Fecha_Lead", "Lead_ID", "Cliente", "Telefono", "Vendedor", "Fuente",
        "Proyecto", "Estado_CRM", "Monto_Separacion", "Observaciones", "Manzana",
        "Lote", "Precio Lista", "Precio venta", "Dscto S/.", "Dscto %",
        "Tipo de Venta", "Inicial", "Saldo", "Fecha firma", "Dias cierre"
    ]
    return _cargar_csv_seguro("cso_ventas.csv", cols, parse_dates=["Fecha_Lead", "Fecha firma"])


def guardar_cso_ventas(df: pd.DataFrame):
    df_save = df.copy()
    if "Vendedor" in df_save.columns:
        df_save["Vendedor"] = df_save["Vendedor"].apply(normalizar_vendedor)
    if "Precio Lista" in df_save.columns and "Precio venta" in df_save.columns:
        df_save["Precio Lista"] = pd.to_numeric(df_save["Precio Lista"], errors="coerce").fillna(0.0)
        df_save["Precio venta"] = pd.to_numeric(df_save["Precio venta"], errors="coerce").fillna(0.0)
        df_save["Inicial"] = pd.to_numeric(df_save.get("Inicial", 0.0), errors="coerce").fillna(0.0)
        df_save["Dscto S/."] = (df_save["Precio Lista"] - df_save["Precio venta"]).clip(lower=0.0)
        df_save["Dscto %"] = np.where(df_save["Precio Lista"] > 0, df_save["Dscto S/."] / df_save["Precio Lista"], 0.0)
        df_save["Saldo"] = (df_save["Precio venta"] - df_save["Inicial"]).clip(lower=0.0)
    df_save.to_csv(os.path.join(DATA_DIR, "cso_ventas.csv"), index=False)


def cargar_cso_cotiz():
    cols = [
        "Fecha_Lead", "Lead_ID", "Cliente", "Telefono", "Vendedor", "Fuente",
        "Proyecto", "Estado_CRM", "Monto_Separacion", "Observaciones", "Manzana",
        "Lote", "Precio Lista", "Precio venta", "Dscto S/.", "Dscto %",
        "Tipo de Venta", "Inicial", "Saldo", "Fecha firma", "Dias cierre"
    ]
    return _cargar_csv_seguro("cso_cotiz.csv", cols, parse_dates=["Fecha_Lead", "Fecha firma"])


def guardar_cso_cotiz(df: pd.DataFrame):
    df_save = df.copy()
    if "Vendedor" in df_save.columns:
        df_save["Vendedor"] = df_save["Vendedor"].apply(normalizar_vendedor)
    df_save.to_csv(os.path.join(DATA_DIR, "cso_cotiz.csv"), index=False)


def cargar_cso_leads():
    cols = [
        "Fecha_Lead", "Lead_ID", "Cliente", "Telefono", "Vendedor", "Estado_CRM",
        "Lote Cotizado", "Monto_Cotizado", "Observaciones", "Fuente", "Proyecto",
        "Campaña", "Vendedor_Kommo", "Etapa_Embudo"
    ]
    return _cargar_csv_seguro("cso_leads.csv", cols, parse_dates=["Fecha_Lead"])


def guardar_cso_leads(df: pd.DataFrame):
    df_save = df.copy()
    if "Vendedor" in df_save.columns:
        df_save["Vendedor"] = df_save["Vendedor"].apply(normalizar_vendedor)
    if "Estado_CRM" in df_save.columns:
        df_save["Etapa_Embudo"] = df_save["Estado_CRM"].apply(normalizar_etapa_crm)
    df_save.to_csv(os.path.join(DATA_DIR, "cso_leads.csv"), index=False)


def cargar_cso_meta():
    cols = ["Mes", "Meta venta S/", "Meta lotes", "Meta cash-in S/", "Presupuesto CSO", "Presupuesto CMO", "Eventos plan"]
    return _cargar_csv_seguro("cso_meta.csv", cols, parse_dates=["Mes"])


def guardar_cso_meta(df: pd.DataFrame):
    df.to_csv(os.path.join(DATA_DIR, "cso_meta.csv"), index=False)


def cargar_cso_asesores():
    cols = ["Vendedor", "Lider", "Estado", "Fecha ingreso", "Meta Unid Mensual"]
    return _cargar_csv_seguro("cso_asesores.csv", cols)


def guardar_cso_asesores(df: pd.DataFrame):
    df_save = df.copy()
    if "Vendedor" in df_save.columns:
        df_save["Vendedor"] = df_save["Vendedor"].apply(normalizar_vendedor)
    df_save.to_csv(os.path.join(DATA_DIR, "cso_asesores.csv"), index=False)


def cargar_cso_costos():
    cols = ["Gasto_ID", "Fecha", "Área", "Categoría", "Detalle / Evento", "Presupuesto", "Real", "Variación S/", "Variación %", "Responsable"]
    return _cargar_csv_seguro("cso_costos.csv", cols, parse_dates=["Fecha"])


def guardar_cso_costos(df: pd.DataFrame):
    df_save = df.copy()
    if "Presupuesto" in df_save.columns and "Real" in df_save.columns:
        df_save["Presupuesto"] = pd.to_numeric(df_save["Presupuesto"], errors="coerce").fillna(0.0)
        df_save["Real"] = pd.to_numeric(df_save["Real"], errors="coerce").fillna(0.0)
        df_save["Variación S/"] = df_save["Real"] - df_save["Presupuesto"]
        df_save["Variación %"] = np.where(df_save["Presupuesto"] > 0, df_save["Variación S/"] / df_save["Presupuesto"], 0.0)
    df_save.to_csv(os.path.join(DATA_DIR, "cso_costos.csv"), index=False)


def cargar_cso_eventos():
    cols = [
        "Evento_ID", "Fecha", "Evento", "Tipo", "Proyecto", "Meta registrados",
        "Registrados real", "Meta asistentes", "Asistentes real", "Conversión meta",
        "Ventas unid. real", "Ticket esperado", "Venta real S/", "Presupuesto",
        "Costo real", "Cash-in proyectado", "Cash-in real"
    ]
    return _cargar_csv_seguro("cso_eventos.csv", cols, parse_dates=["Fecha"])


def guardar_cso_eventos(df: pd.DataFrame):
    df.to_csv(os.path.join(DATA_DIR, "cso_eventos.csv"), index=False)


def cargar_cso_inventario():
    cols = [
        "Lote", "Manzana", "Etapa", "m2", "Precio lista", "Precio actual",
        "Estado", "Fecha liberación", "Fecha venta", "Días disponible",
        "Aging", "N° visitas", "N° cotizaciones", "Demanda", "Próximo precio", "Trigger precio"
    ]
    return _cargar_csv_seguro("cso_inventario.csv", cols, parse_dates=["Fecha liberación", "Fecha venta"])


def guardar_cso_inventario(df: pd.DataFrame):
    df.to_csv(os.path.join(DATA_DIR, "cso_inventario.csv"), index=False)


def cargar_cso_config() -> dict:
    cols = ["Parametro", "Valor", "Descripcion"]
    df = _cargar_csv_seguro("cso_config.csv", cols)
    cfg = {
        "Inicio_Venta": "2025-10-01",
        "Conv_Lead_Agendado": 0.20,
        "Asistencia_Agendado_Visita": 0.60,
        "Conv_Visita_Separacion": 1.0 / 3.0,
        "Conv_Separacion_Venta": 0.80,
        "Ticket_Promedio_Meta": 40000.0,
        "Meta_Ventas_Mensual_Unid": 10.0,
        "Semanas_Operativas_Mes": 4.33,
        "Cash_In_Minimo_Pct": 0.35,
        "Inicial_Promedio_Min_Pct": 0.20,
        "Descuento_Maximo_Pct": 0.04,
        "Cancelaciones_Maximo_Pct": 0.05,
        "Meta_Consolidacion_Pct": 0.95,
        "Capacidad_Leads_Mes_Asesor": 80.0,
    }
    if not df.empty and "Parametro" in df.columns and "Valor" in df.columns:
        for _, row in df.iterrows():
            k = str(row["Parametro"]).strip()
            v = row["Valor"]
            if k == "Inicio_Venta":
                cfg[k] = str(v)
            else:
                try:
                    cfg[k] = float(v)
                except Exception:
                    pass
    return cfg


def cargar_cso_config_df() -> pd.DataFrame:
    cols = ["Parametro", "Valor", "Descripcion"]
    return _cargar_csv_seguro("cso_config.csv", cols)


def guardar_cso_config_df(df: pd.DataFrame):
    df.to_csv(os.path.join(DATA_DIR, "cso_config.csv"), index=False)


# ==============================================================================
# 4. COMPATIBILIDAD HACIA ATRÁS CON EL MVP INICIAL (app.py, Marketing, Finanzas)
# ==============================================================================

def cargar_marketing():
    path = os.path.join(DATA_DIR, "marketing.csv")
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        df = pd.DataFrame({
            "Canal": ["Meta Ads", "Google Ads", "TikTok Ads"],
            "Presupuesto": [21000.0, 5200.0, 7000.0],
            "Leads": [420, 85, 92]
        })
        df.to_csv(path, index=False)
        return df
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame(columns=["Canal", "Presupuesto", "Leads"])


def guardar_marketing(df):
    df.to_csv(os.path.join(DATA_DIR, "marketing.csv"), index=False)


def cargar_ventas():
    """
    Mantiene compatibilidad con core/business_logic.py del MVP gerencial:
    Si ya existen ventas en cso_ventas.csv, proyecta automáticamente las columnas
    Proyecto, Venta_Bruta y Descuento_Pct para que app.py siempre refleje los datos reales.
    """
    df_cso = cargar_cso_ventas()
    if not df_cso.empty and "Precio Lista" in df_cso.columns:
        df_activas = df_cso[df_cso["Estado_CRM"].astype(str).str.strip().str.lower() == "venta"].copy()
        if not df_activas.empty:
            proy = (
                df_activas["Proyecto"].fillna("Proyecto").astype(str)
                + " - Mz " + df_activas["Manzana"].fillna("").astype(str)
                + " Lt " + df_activas["Lote"].fillna("").astype(str)
            )
            return pd.DataFrame({
                "Proyecto": proy,
                "Venta_Bruta": pd.to_numeric(df_activas["Precio Lista"], errors="coerce").fillna(0.0),
                "Descuento_Pct": pd.to_numeric(df_activas["Dscto %"], errors="coerce").fillna(0.0) * 100.0,
            })

    path = os.path.join(DATA_DIR, "ventas.csv")
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        df = pd.DataFrame(columns=["Proyecto", "Venta_Bruta", "Descuento_Pct"])
        df.to_csv(path, index=False)
        return df
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame(columns=["Proyecto", "Venta_Bruta", "Descuento_Pct"])


def guardar_ventas(df):
    df.to_csv(os.path.join(DATA_DIR, "ventas.csv"), index=False)


def cargar_finanzas():
    path = os.path.join(DATA_DIR, "finanzas.csv")
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        df = pd.DataFrame({
            "Categoria": ["Planilla Comercial (CSO)", "Comisiones Ventas", "Movilidad y Eventos", "CRM y Capacitación"],
            "Tipo": ["Fijo", "Variable", "Variable", "Fijo"],
            "Monto": [22000.0, 24500.0, 19850.0, 3600.0]
        })
        df.to_csv(path, index=False)
        return df
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame(columns=["Categoria", "Tipo", "Monto"])


def guardar_finanzas(df):
    df.to_csv(os.path.join(DATA_DIR, "finanzas.csv"), index=False)
