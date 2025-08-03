# forecast_logic.py

import pandas as pd
from prophet import prophet
from tkinter import filedialog
from tkinter.filedialog import asksaveasfilename
from fpdf import FPDF
import matplotlib.pyplot as plt
import tempfile
import os

def forecast_deducciones_y_generar_pdf(json_data):
    # Paso 1: Cargar CSV histórico
    ruta = filedialog.askopenfilename(title="Selecciona CSV histórico de deducciones",
                                      filetypes=[("CSV files", "*.csv")])
    if not ruta:
        return None, "Operación cancelada."

    df_raw = pd.read_csv(ruta, index_col=0)
    df_raw.index.name = "mes"
    df_raw.reset_index(inplace=True)

    # Paso 2: Transformar a formato largo
    df_long = pd.melt(df_raw, id_vars=["mes"], var_name="año", value_name="deduccion")
    df_long = df_long.dropna()

    # Crear fecha sintética para Prophet
    mes_map = {
        'Enero': 1, 'Febrero': 2, 'Marzo': 3, 'Abril': 4,
        'Mayo': 5, 'Junio': 6, 'Julio': 7, 'Agosto': 8,
        'Septiembre': 9, 'Octubre': 10, 'Noviembre': 11, 'Diciembre': 12
    }
    df_long["mes_num"] = df_long["mes"].map(mes_map)
    df_long["ds"] = pd.to_datetime(df_long["año"].astype(str) + "-" + df_long["mes_num"].astype(str) + "-01")
    df_long = df_long.rename(columns={"deduccion": "y"})

    # Paso 3: Ajustar modelo Prophet
    model = Prophet()
    model.fit(df_long[["ds", "y"]])

    # Paso 4: Crear fechas futuras para predicción (solo meses faltantes)
    meses_faltantes = 12 - int(json_data.get("MES", 6))
    last_date = pd.to_datetime(f"{pd.Timestamp.today().year}-{json_data.get('MES', 6)}-01")
    future = pd.date_range(start=last_date, periods=meses_faltantes + 1, freq="MS")[1:]
    future_df = pd.DataFrame({"ds": future})

    forecast = model.predict(future_df)
    forecast = forecast[["ds", "yhat"]]

    # Paso 5: Distribuir DF según proporciones de forecast
    total_forecast = forecast["yhat"].sum()
    if total_forecast == 0:
        return None, "Forecast inválido (todo cero)."

    proporciones = forecast["yhat"] / total_forecast
    total_df = json_data.get("DF", 0)
    forecast["DistribucionDF"] = proporciones * total_df

    # Paso 6: Visualización
    fig, ax = plt.subplots(figsize=(8, 4))
    forecast["mes"] = forecast["ds"].dt.strftime("%b")
    ax.bar(forecast["mes"], forecast["DistribucionDF"])
    ax.set_title("Distribución proyectada de DF por mes")
    ax.set_ylabel("Monto proyectado")
    plt.tight_layout()

    # Guardar imagen temporalmente
    temp_dir = tempfile.gettempdir()
    graph_path = os.path.join(temp_dir, "df_forecast.png")
    fig.savefig(graph_path)
    plt.close()

    # Paso 7: Crear PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Reporte de Tendencia de Deducciones", ln=True, align="C")
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, f"DF Total a distribuir: ${total_df:,.2f}", ln=True)
    pdf.ln(5)
    pdf.image(graph_path, x=10, y=None, w=190)

    ruta_pdf = asksaveasfilename(
        defaultextension=".pdf",
        filetypes=[("Archivo PDF", "*.pdf")],
        title="Guardar reporte de tendencia PDF como..."
    )

    if not ruta_pdf:
        return None, "Guardado cancelado por el usuario."

    try:
        pdf.output(ruta_pdf)
        return ruta_pdf, None
    except Exception as e:
        return None, f"Error al guardar PDF: {str(e)}"
