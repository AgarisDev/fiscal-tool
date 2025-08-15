import pandas as pd
import plotly.graph_objects as go

def forecast_proporcional(ingreso_futuro: float, mes_actual: int, csv_path: str):
    # Leer histórico desde CSV
    df = pd.read_csv(csv_path)

    # Asegurar que las columnas requeridas existen
    if 'Mes' not in df.columns or 'Ingreso' not in df.columns:
        raise ValueError("El CSV debe contener las columnas 'Mes' e 'Ingreso'.")

    # Asegurarse de que 'Mes' sea numérico
    df['Mes'] = pd.to_numeric(df['Mes'], errors='coerce')
    df.dropna(subset=['Mes'], inplace=True)

    # Filtrar meses válidos (1 al 12)
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

    # Calcular proyección mensual basada en el ingreso futuro
    proyeccion = pesos_normalizados * ingreso_futuro

    # Preparar dataframe final
    resultado = pd.DataFrame({
        'Mes': pesos_normalizados.index,
        'Peso (%)': pesos_normalizados.values * 100,
        'Proyección (objetivo)': proyeccion.values
    })

    # Plot con plotly
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=resultado['Mes'],
        y=resultado['Proyección (objetivo)'],
        text=resultado['Peso (%)'].apply(lambda x: f"{x:.1f}%"),
        textposition='outside'
    ))
    fig.update_layout(
        title="Distribución Proporcional del Ingreso Futuro",
        xaxis_title="Mes",
        yaxis_title="Ingreso proyectado",
        template="plotly_dark",
        height=500
    )
    fig.show()
