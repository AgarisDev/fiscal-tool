# logic.py

import pandas as pd
from fpdf import FPDF
from tkinter.filedialog import asksaveasfilename
from tkinter import filedialog

def limpiar_valor(valor):
    if pd.isna(valor):
        return 0.0
    return float(str(valor).replace("$", "").replace(",", "").strip())

def calcular_ingreso_futuro_desde_inputs(cuo, ua, ia, deducciones, mes_actual):
    if mes_actual < 1 or mes_actual > 12:
        return None, "Error: Mes actual debe estar entre 1 y 12"

    try:
        deducciones_finales = deducciones / mes_actual * (12 - mes_actual)
        ingreso_futuro = ((cuo * ia) - ua + deducciones_finales) / (1 - cuo)
        return ingreso_futuro, None
    except ZeroDivisionError:
        return None, "Error: El CUo no puede ser 1."
    except Exception as e:
        return None, f"Error inesperado: {str(e)}"

def cargar_csv_y_generar_pdf():
    ruta = filedialog.askopenfilename(title="Selecciona archivo CSV", filetypes=[("CSV files", "*.csv")])
    if not ruta:
        return None, "Operación cancelada."

    df = pd.read_csv(ruta)

    def preparar_datos(row):
        try:
            row["CUO"] = limpiar_valor(row["Coeficiente objetivo"])
            row["IA"] = limpiar_valor(row["IngresoActual"])
            row["UA"] = limpiar_valor(row["UtilidadActual"])
            row["DA"] = limpiar_valor(row["DeduccionesActuales"])
            row["MES"] = int(row["Mes"])
        except Exception as e:
            print(f"Error preparando datos en fila {row.get('NOMBRE', '')}: {e}")
        return row

    df = df.apply(preparar_datos, axis=1)
    
    def calcular_if(row):
        try:
            dfuturas = row["DA"] / row["MES"] * (12 - row["MES"])
            return round(((row["CUO"] * row["IA"]) - row["UA"] + dfuturas) / (1 - row["CUO"]), 2)
        except Exception as e:
            print(f"Error calculando IF en fila {row.get('NOMBRE', '')}: {e}")
            return None

    df["IngresoFuturo"] = df.apply(calcular_if, axis=1)

    def calcular_df(row):
        try:
            if_val = row.get("IngresoFuturo", 0)
            return round(row["UA"] + if_val - row["CUO"] * (row["IA"] + if_val), 2)
        except Exception as e:
            print(f"Error calculando DF en fila {row.get('NOMBRE', '')}: {e}")
            return None

    df["DF"] = df.apply(calcular_df, axis=1)



    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 12)
    pdf.image("assets/logo.png", x=10, y=8, w=30)
    pdf.cell(0, 10, "Reporte Financiero", border=0, ln=True, align="C")
    pdf.ln(15)

    pdf.set_font("Arial", size=10)
    columnas = ["NOMBRE", "RFC", "IngresoFuturo","DF"]
    col_widths = [60, 40, 40,40]

    for i, col in enumerate(columnas):
        pdf.cell(col_widths[i], 10, col, border=1)
    pdf.ln()

    for _, row in df.iterrows():
        for i, col in enumerate(columnas):
            pdf.cell(col_widths[i], 10, str(row.get(col, ""))[:15], border=1)
        pdf.ln()

    ruta_salida = asksaveasfilename(
    defaultextension=".pdf",
    filetypes=[("Archivo PDF", "*.pdf")],
    title="Guardar reporte PDF como..."
    )

    if not ruta_salida:
        return None, "Guardado cancelado por el usuario."

    try:
        pdf.output(ruta_salida)
        return ruta_salida, None
    except Exception as e:
        return None, f"Error al guardar PDF: {str(e)}"

   # pdf.output("reporte_ingresos_futuros.pdf")
    #return "reporte_ingresos_futuros.pdf", None
