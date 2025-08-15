# logic.py

import pandas as pd
from fpdf import FPDF
from tkinter.filedialog import asksaveasfilename
from tkinter import filedialog
import os
import json

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



    def calcular_ca_co(row):
        try:
            ca = row["UA"] / row["IA"] if row["IA"] != 0 else 0
            co = row["CUO"]
            return f"{ca:.4f} / {co:.4f}"
        except Exception as e:
            print(f"Error calculando Ca / Co en fila {row.get('NOMBRE', '')}: {e}")
            return ""
        
    df["Ca / Co"] = df.apply(calcular_ca_co, axis=1)

    def guardar_resultados_en_json(df, archivo_json="resultados.json"):
    # Borrar archivo si ya existe
        if os.path.exists(archivo_json):
            os.remove(archivo_json)

        resultados = []
        for _, row in df.iterrows():
            try:
                nombre = row.get("NOMBRE", "")
                df_val = round(row.get("DF", 0), 2)
                if_val = round(row.get("IngresoFuturo", 0), 2)
                co_val = round(row.get("CUO", 0), 4)
                ia = row.get("IA", 0)
                ua = row.get("UA", 0)
                ca_val = f"{ua / ia:.4f}" if ia != 0 else "0.0000"
                meses_restantes = 12 - row.get("Mes",0) 

                resultados.append({
                    "NOMBRE": nombre,
                    "DF": df_val,
                    "IF": if_val,
                    "CO": co_val,
                    "CA": ca_val,
                    "MES": meses_restantes
                })
            except Exception as e:
                print(f"Error exportando a JSON fila {nombre}: {e}")

        with open(archivo_json, "w", encoding="utf-8") as f:
            json.dump(resultados, f, indent=4, ensure_ascii=False)

    class CustomPDF(FPDF):
        def header(self):
            # Fondo oscuro para cada página
            self.set_fill_color(26, 26, 26)
            self.rect(0, 0, 210, 297, 'F')

            # Logo
            self.image("assets/logo.png", x=10, y=8, w=30)

            # Título
            self.set_text_color(255, 255, 255)
            self.set_font("Arial", "B", 12)
            self.cell(0, 10, "Reporte Financiero", border=0, ln=True, align="C")
            self.ln(10)

            # Encabezado de tabla en todas las páginas
            self.set_font("Arial", size=10)
            self.set_fill_color(40, 40, 40)
            for i, col in enumerate(columnas):
                self.cell(col_widths[i], 10, col, border=1, fill=True)
            self.ln()

        def footer(self):
            self.set_y(-15)
            self.set_font("Arial", "I", 8)
            self.set_text_color(180, 180, 180)
            self.cell(0, 10, f"Página {self.page_no()}", align="C")

    # Columnas y anchos
    columnas = ["NOMBRE", "RFC", "IngresoFuturo", "DF", "Ca / Co"]
    col_widths = [70, 30, 30, 30,30]

    # Crear PDF
    pdf = CustomPDF()
    pdf.add_page()
    pdf.set_margins(left=10, top=40, right=10)
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.set_font("Arial", size=10)
    pdf.set_text_color(255, 255, 255)

    # Zebra rows
    zebra_colors = [(30, 30, 30), (50, 50, 50)]
    for idx, (_, row) in enumerate(df.iterrows()):
        if pdf.get_y() > 265:  # Aproximadamente al final de página
            pdf.add_page()
        r, g, b = zebra_colors[idx % 2]
        pdf.set_fill_color(r, g, b)
        for i, col in enumerate(columnas):
            pdf.cell(col_widths[i], 10, str(row.get(col, ""))[:15], border=1, fill=True)
        pdf.ln()

    # Guardar el PDF
    ruta_salida = asksaveasfilename(
        defaultextension=".pdf",
        filetypes=[("Archivo PDF", "*.pdf")],
        title="Guardar reporte PDF como..."
    )

    if not ruta_salida:
        return None, "Guardado cancelado por el usuario."

    try:
        pdf.output(ruta_salida)
        guardar_resultados_en_json(df)
        return ruta_salida, None
    
    except Exception as e:
        return None, f"Error al guardar PDF: {str(e)}"
