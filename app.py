import streamlit as st
import pandas as pd
from scipy.stats import poisson

# Configuración visual
st.set_page_config(page_title="Predicciones Mundial 2026", page_icon="⚽")

# Título y Estilo
st.title("⚽ Simulador de Resultados: Mundial")
st.sidebar.header("Configuración del Modelo")

# Variable de ajuste: ¿Es un mundial con muchos o pocos goles?
sensibilidad = st.sidebar.slider("Factor de ofensiva global", 0.5, 2.0, 1.0)

# Datos de ejemplo (Esto lo podrías cargar desde un Excel/CSV)
data = {
    "Argentina": {"ataque": 1.8, "defensa": 0.5},
    "Francia": {"ataque": 1.7, "defensa": 0.6},
    "Brasil": {"ataque": 1.6, "defensa": 0.5},
    "España": {"ataque": 1.5, "defensa": 0.8}
}

def predecir(local, visitante):
    # Lógica de Poisson ajustada por la defensa del rival
    lambda_local = data[local]["ataque"] * data[visitante]["defensa"] * sensibilidad
    lambda_visit = data[visitante]["ataque"] * data[local]["defensa"] * sensibilidad
    
    goles_local = poisson.rvs(lambda_local) # rvs genera un número aleatorio basado en la prob.
    goles_visit = poisson.rvs(lambda_visit)
    return goles_local, goles_visit

# UI de Predicción
col1, col2 = st.columns(2)
with col1:
    team_a = st.selectbox("Equipo Local", list(data.keys()), index=0)
with col2:
    team_b = st.selectbox("Equipo Visitante", list(data.keys()), index=1)

if st.button("🚀 Simular Partido"):
    g_a, g_b = predecir(team_a, team_b)
    
    st.markdown(f"""
    <div style='text-align: center; font-size: 40px; font-weight: bold; background-color: #f0f2f6; padding: 20px; border-radius: 10px;'>
        {team_a} {g_a} - {g_b} {team_b}
    </div>
    """, unsafe_allow_html=True)

    if g_a > g_b:
        st.success(f"🏆 Ganador: {team_a}")
    elif g_b > g_a:
        st.success(f"🏆 Ganador: {team_b}")
    else:
        st.warning("🤝 Empate")