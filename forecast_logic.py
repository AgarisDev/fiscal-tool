import pandas as pd
import plotly.graph_objects as go

def forecast_proporcional(ingreso_futuro: float, deducciones_futuras: float, mes_actual: int, csv_path: str):
    # Leer histórico desde CSV
    df = pd.read_csv(csv_path)

    # Asegurar que las columnas requeridas existen
    if 'Mes' not in df.columns or 'Ingreso' not in df.columns:
        raise ValueError("El CSV debe contener las columnas 'Mes' e 'Ingreso'.")

    # Convertir 'Mes' a numérico y filtrar datos válidos
    df['Mes'] = pd.to_numeric(df['Mes'], errors='coerce')
    df.dropna(subset=['Mes'], inplace=True)
    df = df[(df['Mes'] >= 1) & (df['Mes'] <= 12)]

    # Agrupar por mes y obtener promedio histórico
    historial_promedio = df.groupby('Mes')['Ingreso'].mean()

    # Determinar los meses restantes
    meses_restantes = list(range(mes_actual + 1, 13))
    if not meses_restantes:
        raise ValueError("No quedan meses por proyectar este año.")

    # Extraer promedios de meses restantes
    pesos = historial_promedio.loc[meses_restantes]

    # Normalizar a porcentajes
    total = pesos.sum()
    if total == 0:
        raise ValueError("Los valores históricos están vacíos o son todos ceros.")
    pesos_normalizados = pesos / total

    # Calcular proyecciones para IF y DF
    proyeccion_if = pesos_normalizados * ingreso_futuro
    proyeccion_df = pesos_normalizados * deducciones_futuras

    # DataFrame final
    resultado = pd.DataFrame({
        'Mes': pesos_normalizados.index,
        'Peso (%)': pesos_normalizados.values * 100,
        'Proyección Ingreso Futuro': proyeccion_if.values,
        'Proyección Deducciones Futuras': proyeccion_df.values
    })

    # Crear gráfico comparativo
    fig = go.Figure()

    # Serie de IF
    fig.add_trace(go.Bar(
        x=resultado['Mes'],
        y=resultado['Proyección Ingreso Futuro'],
        name="Ingreso Futuro",
        marker_color='lightgreen',
        text=resultado['Peso (%)'].apply(lambda x: f"{x:.1f}%"),
        textposition='outside'
    ))

    # Serie de DF
    fig.add_trace(go.Bar(
        x=resultado['Mes'],
        y=resultado['Proyección Deducciones Futuras'],
        name="Deducciones Futuras",
        marker_color='tomato',
        textposition='outside'
    ))

    fig.update_layout(
        title="Distribución Proporcional de Ingreso y Deducciones Futuras",
        xaxis_title="Mes",
        yaxis_title="Monto proyectado",
        template="plotly_dark",
        barmode='group',
        height=500
    )

    # Guardar como HTML
    html_path = "forecast_result.html"
    fig.write_html(html_path)
    return html_path, resultado
