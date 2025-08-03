# forecast_logic.py
import pandas as pd
import plotly.graph_objects as go
import calendar
import os
from datetime import datetime

def generar_distribucion_normal(nombre_empresa, ingreso_futuro, mes_actual, ruta_csv_historico, carpeta_salida):
    try:
        # Leer el CSV
        df = pd.read_csv(ruta_csv_historico)

        # Validar columnas
        if not {'AÑO', 'MES', 'NOMBRE', 'INGRESO'}.issubset(df.columns):
            return None, "El CSV debe contener las columnas: AÑO, MES, NOMBRE, INGRESO"

        # Filtrar por empresa
        df_empresa = df[df['NOMBRE'] == nombre_empresa]
        if df_empresa.empty:
            return None, f"No hay datos históricos para la empresa: {nombre_empresa}"

        # Agrupar ingresos por mes en todos los años
        ingresos_por_mes = df_empresa.groupby('MES')['INGRESO'].sum()

        # Calcular proporciones históricas por mes
        total_ingresos = ingresos_por_mes.sum()
        proporciones = ingresos_por_mes / total_ingresos

        # Filtrar meses restantes
        meses_restantes = list(range(mes_actual, 13))  # 1-based months
        proporciones_restantes = proporciones.loc[meses_restantes]
        proporciones_normalizadas = proporciones_restantes / proporciones_restantes.sum()

        # Distribuir ingreso futuro según proporciones normalizadas
        distribucion = ingreso_futuro * proporciones_normalizadas

        # Crear tabla para mostrar
        resultados_df = pd.DataFrame({
            'Mes': [calendar.month_name[m] for m in meses_restantes],
            'Proporcion': proporciones_normalizadas.values,
            'Ingreso Asignado': distribucion.values
        })

        # Generar HTML con Plotly
        fig = go.Figure(data=[
            go.Bar(x=resultados_df['Mes'], y=resultados_df['Ingreso Asignado'], name='Ingreso Proyectado')
        ])
        fig.update_layout(title=f"Distribución proyectada de ingresos - {nombre_empresa}", xaxis_title="Mes", yaxis_title="Ingreso ($)")

        # Guardar HTML
        nombre_archivo = f"forecast_{nombre_empresa.replace(' ', '_')}.html"
        ruta_salida = os.path.join(carpeta_salida, nombre_archivo)
        fig.write_html(ruta_salida, auto_open=False)

        return ruta_salida, None

    except Exception as e:
        return None, str(e)
