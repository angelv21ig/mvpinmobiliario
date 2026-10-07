import os
import pandas as pd

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
os.makedirs(DATA_DIR, exist_ok=True)

# ----------------- MARKETING -----------------
def cargar_marketing():
    path = os.path.join(DATA_DIR, "marketing.csv")
    if not os.path.exists(path):
        df = pd.DataFrame({
            "Canal": ["Meta Ads", "Google Ads", "Portales Inmobiliarios", "Ferias"],
            "Presupuesto": [4500.0, 6000.0, 3200.0, 1500.0],
            "Leads": [120, 140, 80, 25]
        })
        df.to_csv(path, index=False)
    return pd.read_csv(path)

def guardar_marketing(df):
    path = os.path.join(DATA_DIR, "marketing.csv")
    df.to_csv(path, index=False)

# ----------------- VENTAS -----------------
def cargar_ventas():
    path = os.path.join(DATA_DIR, "ventas.csv")
    if not os.path.exists(path):
        df = pd.DataFrame({
            "Proyecto": ["Depa 301 - Miraflores", "Oficina 502 - San Isidro", "Lote 14 - Cieneguilla"],
            "Venta_Bruta": [180000.0, 120000.0, 65000.0],
            "Descuento_Pct": [5.0, 0.0, 10.0]
        })
        df.to_csv(path, index=False)
    return pd.read_csv(path)

def guardar_ventas(df):
    path = os.path.join(DATA_DIR, "ventas.csv")
    df.to_csv(path, index=False)

# ----------------- FINANZAS -----------------
def cargar_finanzas():
    path = os.path.join(DATA_DIR, "finanzas.csv")
    if not os.path.exists(path):
        df = pd.DataFrame({
            "Categoria": ["Planilla Comercial", "Comisiones Asesores", "Mantenimiento / Operativos"],
            "Tipo": ["Fijo", "Variable", "Fijo"],
            "Monto": [18000.0, 8500.0, 3200.0]
        })
        df.to_csv(path, index=False)
    return pd.read_csv(path)

def guardar_finanzas(df):
    path = os.path.join(DATA_DIR, "finanzas.csv")
    df.to_csv(path, index=False)



if __name__ == "__main__":
    print("Probando carga de datos...")
    print(cargar_marketing().head(2))
    print(cargar_ventas().head(2))
    print(cargar_finanzas().head(2))
    print("¡Base y data_manager listos!")



# Mejora de robustez en core/data_manager.py
def cargar_ventas():
    path = os.path.join(DATA_DIR, "ventas.csv")
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        df = pd.DataFrame(columns=["Proyecto", "Venta_Bruta", "Descuento_Pct"])
        df.to_csv(path, index=False)
        return df
    try:
        return pd.read_csv(path)
    except Exception:
        # En caso de archivo corrupto, inicializar estructura base
        return pd.DataFrame(columns=["Proyecto", "Venta_Bruta", "Descuento_Pct"])