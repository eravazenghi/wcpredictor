import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import poisson

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Simulador Mundial 2026", page_icon="⚽", layout="wide")

# --- CARGA DE DATOS SEGURA ---
@st.cache_data
def cargar_datos():
    try:
        df = pd.read_csv("equipos.csv")
        df.columns = df.columns.str.strip()
        df['Pais'] = df['Pais'].str.strip()
        return df.set_index("Pais").to_dict(orient="index")
    except FileNotFoundError:
        st.error("Error: No se encontró el archivo 'equipos.csv'. Asegúrate de subirlo a GitHub junto a este archivo.")
        return {}

data = cargar_datos()

# --- MOTOR DE PREDICCIÓN ---
def predecir_partido(local, visitante):
    PROMEDIO_GOLES = 1.35
    
    # Validación de seguridad: si el equipo no existe en el CSV, usamos valores por defecto para que no explote
    if local not in data or visitante not in data:
        return 1, 1
        
    lambda_local = data[local]["ataque"] * data[visitante]["defensa"] * PROMEDIO_GOLES
    lambda_visit = data[visitante]["ataque"] * data[local]["defensa"] * PROMEDIO_GOLES
    
    goles_local = int(np.argmax([poisson.pmf(i, lambda_local) for i in range(7)]))
    goles_visit = int(np.argmax([poisson.pmf(i, lambda_visit) for i in range(7)]))
    
    return goles_local, goles_visit

def resolver_partido_eliminatorio(local, visitante):
    g_l, g_v = predecir_partido(local, visitante)
    if g_l > g_v:
        return local, f"{g_l} - {g_v}"
    elif g_v > g_l:
        return visitante, f"{g_l} - {g_v}"
    else:
        # Desempate seguro por Elo histórico
        elo_local = data[local]['Elo'] if local in data else 1500
        elo_visit = data[visitante]['Elo'] if visitante in data else 1500
        ganador = local if elo_local > elo_visit else visitante
        return ganador, f"{g_l} - {g_v} (Pen.)"

# --- INTERFAZ DE USUARIO (UI) ---
st.title("🏆 Simulador Inteligente - Mundial 2026")
st.markdown("Predicciones de alta precisión usando *Distribución de Poisson* y *Ranking Elo*.")

if data:
    tab1, tab2 = st.tabs(["📊 Partido Individual", "🌿 Llaves del Torneo (Playoffs)"])
    
    # ---------------------------------------------------------
    # PESTAÑA 1: PARTIDO INDIVIDUAL
    # ---------------------------------------------------------
    with tab1:
        st.subheader("Simular cualquier enfrentamiento")
        lista_equipos = sorted(list(data.keys()))
        
        col1, col2 = st.columns(2)
        with col1:
            equipo_a = st.selectbox("Equipo Local", lista_equipos, index=lista_equipos.index("Argentina") if "Argentina" in lista_equipos else 0)
        with col2:
            equipo_b = st.selectbox("Equipo Visitante", lista_equipos, index=lista_equipos.index("Francia") if "Francia" in lista_equipos else 1)
            
        if st.button("🚀 Calcular Pronóstico", use_container_width=True):
            if equipo_a == equipo_b:
                st.warning("Selecciona dos selecciones diferentes.")
            else:
                g_a, g_b = predecir_partido(equipo_a, equipo_b)
                st.markdown(f"""
                <div style='text-align: center; font-size: 40px; font-weight: bold; background-color: #1e293b; color: white; padding: 20px; border-radius: 12px; margin: 15px 0;'>
                    {equipo_a} <span style='color: #38bdf8;'>{g_a}</span> &nbsp;-&nbsp; <span style='color: #38bdf8;'>{g_b}</span> {equipo_b}
                </div>
                """, unsafe_allow_html=True)
                
                if g_a > g_b: st.success(f"🎉 **Ganador proyectado:** {equipo_a}")
                elif g_b > g_a: st.success(f"🎉 **Ganador proyectado:** {equipo_b}")
                else:
                    elo_a = data[equipo_a]['Elo'] if equipo_a in data else 1500
                    elo_b = data[equipo_b]['Elo'] if equipo_b in data else 1500
                    ganador_e = equipo_a if elo_a > elo_b else equipo_b
                    st.info(f"🤝 **Empate en los 90'.** Por balance de Ranking Elo, avanza en penales: **{ganador_e}**")

    # ---------------------------------------------------------
    # PESTAÑA 2: LLAVES DEL MUNDIAL (PROYECCIÓN COMPLETA)
    # ---------------------------------------------------------
    with tab2:
        st.subheader("Simulación del Cuadro Final (48 Equipos - Clasificados a 16avos)")
        st.write("Estructura proyectada con las 32 mejores selecciones basadas en rendimiento previo.")
        
        # CORREGIDO: Lista exacta de 32 equipos únicos presentes en tu equipos.csv
        llaves_16avos = [
            ("Argentina", "Nigeria"), ("México", "Alemania"),
            ("Francia", "Egipto"), ("Uruguay", "Corea del Sur"),
            ("España", "Ecuador"), ("Países Bajos", "Irán"),
            ("Brasil", "Canadá"), ("Colombia", "Australia"),
            ("Inglaterra", "Marruecos"), ("Bélgica", "Estados Unidos"),
            ("Portugal", "Argelia"), ("Croacia", "Japón"),
            ("Italia", "Senegal"), ("Suiza", "Ucrania"),
            ("Dinamarca", "Austria"), ("Costa de Marfil", "Túnez")
        ]
        
        if st.button("🔮 Correr Simulación Completa del Mundial", type="primary", use_container_width=True):
            
            # --- 16AVOS DE FINAL ---
            st.markdown("### 🏟️ Dieciseisavos de Final")
            ganadores_16avos = []
            cols = st.columns(4)
            for i, cruce in enumerate(llaves_16avos):
                ganador, res = resolver_partido_eliminatorio(cruce[0], cruce[1])
                ganadores_16avos.append(ganador)
                with cols[i % 4]:
                    st.caption(f"Partido {i+1}")
                    st.markdown(f"**{cruce[0]}** vs **{cruce[1]}**\n`Resultado: {res}`\n👉 **Avanza: {ganador}**")
            
            # --- OCTAVOS DE FINAL ---
            st.markdown("---")
            st.markdown("### 🧪 Octavos de Final")
            llaves_octavos = [(ganadores_16avos[i], ganadores_16avos[i+1]) for i in range(0, len(ganadores_16avos), 2)]
            ganadores_octavos = []
            cols = st.columns(4)
            for i, cruce in enumerate(llaves_octavos):
                ganador, res = resolver_partido_eliminatorio(cruce[0], cruce[1])
                ganadores_octavos.append(ganador)
                with cols[i % 4]:
                    st.markdown(f"**{cruce[0]}** vs **{cruce[1]}**\n`Resultado: {res}`\n👉 **Avanza: {ganador}**")

            # --- CUARTOS DE FINAL ---
            st.markdown("---")
            st.markdown("### 📉 Cuartos de Final")
            llaves_cuartos = [(ganadores_octavos[i], ganadores_octavos[i+1]) for i in range(0, len(ganadores_octavos), 2)]
            ganadores_cuartos = []
            cols = st.columns(2)
            for i, cruce in enumerate(llaves_cuartos):
                ganador, res = resolver_partido_eliminatorio(cruce[0], cruce[1])
                ganadores_cuartos.append(ganador)
                with cols[i % 2]:
                    st.markdown(f"📦 **{cruce[0]}** vs **{cruce[1]}**\n`Resultado: {res}`\n👉 **Avanza: {ganador}**")

            # --- SEMIFINALES ---
            st.markdown("---")
            st.markdown("### 📢 Semifinales")
            llaves_semis = [(ganadores_cuartos[i], ganadores_cuartos[i+1]) for i in range(0, len(ganadores_cuartos), 2)]
            ganadores_semis = []
            cols = st.columns(2)
            for i, cruce in enumerate(llaves_semis):
                ganador, res = resolver_partido_eliminatorio(cruce[0], cruce[1])
                ganadores_semis.append(ganador)
                with cols[i % 2]:
                    st.markdown(f"🔥 **{cruce[0]}** vs **{cruce[1]}**\n`Resultado: {res}`\n👉 **FUTURO FINALISTA: {ganador}**")

            # --- GRAN FINAL ---
            st.markdown("---")
            st.markdown("<h2 style='text-align: center; color: #f59e0b;'>🏆 GRAN FINAL DEL MUNDIAL 🏆</h2>", unsafe_allow_html=True)
            campeon, res_final = resolver_partido_eliminatorio(ganadores_semis[0], ganadores_semis[1])
            
            st.markdown(f"""
            <div style='text-align: center; font-size: 35px; font-weight: bold; background-color: #f59e0b; color: black; padding: 30px; border-radius: 15px; margin-top: 10px;'>
                {ganadores_semis[0]} {res_final} {ganadores_semis[1]}
                <br><br>
                ⭐ ¡CAMPEÓN DEL MUNDO: {campeon.upper()}! ⭐
            </div>
            """, unsafe_allow_html=True)
