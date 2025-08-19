# forecast_logic.py

import os
import json
import pandas as pd
import plotly.graph_objects as go
from typing import Tuple, Optional, List

MESES = {
    1: "Enero",
    2: "Febrero",
    3: "Marzo",
    4: "Abril",
    5: "Mayo",
    6: "Junio",
    7: "Julio",
    8: "Agosto",
    9: "Septiembre",
    10: "Octubre",
    11: "Noviembre",
    12: "Diciembre"
}


def _to_float(x, default: float = 0.0) -> float:
    try:
        return float(x)
    except Exception:
        return default


def _cargar_pesos_historicos(hist_csv_path: str) -> Tuple[pd.Series, pd.Series]:
    """
    Lee el CSV histórico (columnas esperadas: año, Mes, Ingreso, deducciones)
    y devuelve DOS Series con índice 1..12:
      - pesos_ingreso[mes]: peso normalizado por mes para INGRESO
      - pesos_deducciones[mes]: peso normalizado por mes para DEDUCCIONES
    Si el total de alguna métrica es 0, usa distribución uniforme 1/12.
    """
    if not os.path.exists(hist_csv_path):
        raise FileNotFoundError(f"No se encontró el CSV histórico: {hist_csv_path}")

    hist = pd.read_csv(hist_csv_path)

    # Normalizar nombres de columnas a minúsculas para robustez
    cols_lower = {c: c.lower() for c in hist.columns}
    hist.rename(columns=cols_lower, inplace=True)

    # Mapear nombres esperados
    col_mes = None
    for candidate in ("mes",):
        if candidate in hist.columns:
            col_mes = candidate
            break

    col_ing = None
    for candidate in ("ingreso", "ingresos"):
        if candidate in hist.columns:
            col_ing = candidate
            break

    col_ded = None
    for candidate in ("deducciones", "deduccion", "ded"):
        if candidate in hist.columns:
            col_ded = candidate
            break

    faltantes = [n for n, v in {"Mes": col_mes, "Ingreso": col_ing, "deducciones": col_ded}.items() if v is None]
    if faltantes:
        raise ValueError(f"El CSV histórico debe contener columnas: {faltantes}. "
                         f"Columnas encontradas: {list(hist.columns)}")

    # Tipificar
    hist[col_mes] = pd.to_numeric(hist[col_mes], errors="coerce")
    hist[col_ing] = pd.to_numeric(hist[col_ing], errors="coerce")
    hist[col_ded] = pd.to_numeric(hist[col_ded], errors="coerce")

    hist = hist.dropna(subset=[col_mes])
    hist = hist[(hist[col_mes] >= 1) & (hist[col_mes] <= 12)]

    # Agrupar por mes y sumar
    monthly_ing = hist.groupby(col_mes)[col_ing].sum().reindex(range(1, 13), fill_value=0.0)
    monthly_ded = hist.groupby(col_mes)[col_ded].sum().reindex(range(1, 13), fill_value=0.0)

    # Normalizar a pesos
    total_ing = monthly_ing.sum()
    total_ded = monthly_ded.sum()

    if total_ing == 0:
        pesos_ing = pd.Series([1.0 / 12] * 12, index=range(1, 13), dtype=float)
    else:
        pesos_ing = monthly_ing / total_ing

    if total_ded == 0:
        pesos_ded = pd.Series([1.0 / 12] * 12, index=range(1, 13), dtype=float)
    else:
        pesos_ded = monthly_ded / total_ded

    return pesos_ing, pesos_ded

def forecast_proporcional(
    json_path: str,
    hist_csv_path: str,
    nombre_empresa: Optional[str] = None
):

    if not os.path.exists(json_path):
        raise FileNotFoundError(f"No se encontró el JSON: {json_path}")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    df = pd.DataFrame(data)

    requeridas = ["NOMBRE", "IF", "DF", "CO", "CA", "MES", "IA", "UA", "DA"]
    falt = [c for c in requeridas if c not in df.columns]
    if falt:
        raise ValueError(f"Faltan columnas en el JSON: {falt}")

    if nombre_empresa:
        df = df[df["NOMBRE"] == nombre_empresa]
        if df.empty:
            raise ValueError(f"No se encontró la empresa '{nombre_empresa}' en {json_path}.")

    pesos_ing, pesos_ded = _cargar_pesos_historicos(hist_csv_path)

    resultados: list[tuple[str, pd.DataFrame]] = []

    for _, row in df.iterrows():
        nombre = str(row["NOMBRE"])
        ingreso_futuro = _to_float(row["IF"], 0.0)
        deducciones_futuras = _to_float(row["DF"], 0.0)
        coef_objetivo = _to_float(row["CO"], 0.0)
        ingreso_actual = _to_float(row["IA"], 0.0)
        utilidad_actual = _to_float(row["UA"], 0.0)
        deducciones_actuales = _to_float(row["DA"], 0.0)
        meses_restantes = int(_to_float(row["MES"], 0.0))

        if meses_restantes <= 0:
            continue

        mes_actual = 12 - meses_restantes
        meses_a_proyectar = list(range(mes_actual + 1, 13))
        if not meses_a_proyectar:
            continue

        w_if = pesos_ing.loc[meses_a_proyectar]
        w_df = pesos_ded.loc[meses_a_proyectar]

        w_if = w_if / w_if.sum() if w_if.sum() != 0 else pd.Series([1.0 / len(meses_a_proyectar)] * len(meses_a_proyectar), index=meses_a_proyectar)
        w_df = w_df / w_df.sum() if w_df.sum() != 0 else pd.Series([1.0 / len(meses_a_proyectar)] * len(meses_a_proyectar), index=meses_a_proyectar)

        proy_if = ingreso_futuro * w_if
        proy_df = deducciones_futuras * w_df
        coef_utilidad_actual = (utilidad_actual / ingreso_actual) if ingreso_actual != 0 else 0.0

        resultado = pd.DataFrame({
            "Mes": list(w_if.index.astype(int)),
            "Peso_IF (%)": (w_if.values * 100.0),
            "Proyección_IF": proy_if.values,
            "Peso_DF (%)": (w_df.values * 100.0),
            "Proyección_DF": proy_df.values
        })
        resultado["Mes_nombre"] = resultado["Mes"].map(MESES)

        # --- Gráficos ---
        fig = go.Figure()
        fig.add_trace(go.Bar(x=resultado["Mes"], y=resultado["Proyección_IF"], name="Distribución de ingreso mensual"))
        fig.add_trace(go.Bar(x=resultado["Mes"], y=resultado["Proyección_DF"], name="Facturación mensual requerida"))
        fig.update_layout(title=f"Proyección mensual - {nombre}", barmode="group",
                          template="plotly_dark", height=500, xaxis_title="Mes", yaxis_title="Monto")

        fig_weights = go.Figure()
        fig_weights.add_trace(
            go.Scatter(x=resultado["Mes"], y=resultado["Peso_IF (%)"], mode="lines+markers",
                       name="Peso IF (%)", line=dict(color="cyan", width=2),
                       marker=dict(symbol="circle", size=8),
                       hovertemplate="Mes: %{customdata}<br>Peso IF: %{y:.2f}%<extra></extra>",
                       customdata=resultado["Mes_nombre"])
        )
        fig_weights.add_trace(
            go.Scatter(x=resultado["Mes"], y=resultado["Peso_DF (%)"], mode="lines+markers",
                       name="Peso DF (%)", line=dict(color="magenta", width=2),
                       marker=dict(symbol="diamond", size=10),
                       hovertemplate="Mes: %{customdata}<br>Peso DF: %{y:.2f}%<extra></extra>",
                       customdata=resultado["Mes_nombre"])
        )
        fig_weights.update_layout(title=f"Distribución de Pesos - {nombre}",
                                  template="plotly_dark", height=400, xaxis_title="Mes", yaxis_title="Peso (%)")

        # --- HTML Dashboard ---
        html_path = os.path.join(os.getcwd(), f"forecast_{nombre.replace(' ', '_')}.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(f"""
<html>
<head>
    <style>
        body {{
            background-color: #121212;
            color: #e0e0e0;
            font-family: Arial, sans-serif;
            margin: 20px;
        }}
        .header-container {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 30px;
        }}
        h1 {{
            color: #d3d3d3;
            font-size: 28px;
            margin: 0;
        }}
        img.logo {{
            height: 60px;
        }}
        .metrics-container {{
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
            margin-bottom: 30px;
        }}
        .metric-card {{
            background-color: #1e1e1e;
            border-radius: 10px;
            padding: 20px 25px;
            flex: 1 1 250px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.5);
            font-size: 18px;
        }}
        .metric-card b {{
            color: #ff69b4;
        }}
        .plot-container {{
            margin: 20px 0;
        }}
        @media (max-width: 800px) {{
            .metrics-container {{
                flex-direction: column;
            }}
        }}
    </style>
</head>
<body>
    <div class="header-container">
        <h1>{nombre}</h1>
        <img class="logo" src="assets/logo.png" alt="Logo">
    </div>

    <div class="metrics-container">
        <div class="metric-card"><b>Coeficiente objetivo:</b> {coef_objetivo:.6f}</div>
        <div class="metric-card"><b>Total deducciones actuales:</b> {deducciones_actuales:,.2f}</div>
        <div class="metric-card"><b>Total ingreso actual:</b> {ingreso_actual:,.2f}</div>
        <div class="metric-card"><b>Total ingreso futuro (IF):</b> {ingreso_futuro:,.2f}</div>
        <div class="metric-card"><b>Total deducciones futuras (DF):</b> {deducciones_futuras:,.2f}</div>
        <div class="metric-card"><b>Coeficiente utilidad actual:</b> {coef_utilidad_actual:.6f}</div>
    </div>

    <div class="plot-container">
""")
            f.write(fig.to_html(full_html=False, include_plotlyjs='cdn'))
            f.write("</div><div class='plot-container'>")
            f.write(fig_weights.to_html(full_html=False, include_plotlyjs=False))
            f.write("</div></body></html>")

        resultados.append((html_path, resultado))

    return resultados[0] if nombre_empresa else resultados

