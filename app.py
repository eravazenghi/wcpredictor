import streamlit as st
import pandas as pd
from scipy.stats import poisson

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Simulador Mundial 2026", page_icon="⚽", layout="wide")

# --- CARGA DE DATOS SEGURA ---
@st.cache_data
def cargar_datos():
    try:
        # Leemos el CSV original
        df = pd.read_csv("equipos.csv")
        
        # Normalizamos los nombres de las columnas a minúsculas y limpiamos espacios
        df.columns = df.columns.str.strip().str.lower()
        
        # Nos aseguramos de que los nombres de los países sean texto limpio
        df['pais'] = df['pais'].astype(str).str.strip()
        
        # Descartamos filas con datos faltantes (NaN) en las columnas clave
        df = df.dropna(subset=["pais", "ataque", "defensa", "elo"])
        
        # Ordenamos por Elo jerárquico de mayor a menor para armar las llaves
        df = df.sort_values(by="elo", ascending=False)
        
        # Retornamos el diccionario indexado por país
        return df.set_index("pais").to_dict(orient="index")
    except Exception as e:
        st.error(f"Error al cargar 'equipos.csv': {e}")
        return {}

data = cargar_datos()

# --- MOTOR DE PREDICCIÓN ---
def predecir_partido(local, visitante):
    PROMEDIO_GOLES = 1.35
    
    # Control de contingencia absoluto por si un string no coincide
    if local not in data or visitante not in data:
        return 1, 0
        
    try:
        # Usamos las claves en minúsculas estrictas tal como las normalizó la carga de datos
        lambda_local = float(data[local]["ataque"]) * float(data[visitante]["defensa"]) * PROMEDIO_GOLES
        lambda_visit = float(data[visitante]["ataque"]) * float(data[local]["defensa"]) * PROMEDIO_GOLES
    except (TypeError, ValueError):
        lambda_local, lambda_visit = 1.2, 1.0
    
    # Calculamos las probabilidades para goles de 0 a 6
    probs_local = [poisson.pmf(i, lambda_local) for i in range(7)]
    probs_visit = [poisson.pmf(i, lambda_visit) for i in range(7)]
    
    # Buscamos el índice del valor máximo usando Python nativo (así evitamos conflictos de versiones de numpy)
    goles_local = probs_local.index(max(probs_local))
    goles_visit = probs_visit.index(max(probs_visit))
    
    return goles_local, goles_visit

def resolver_partido_eliminatorio(local, visitante):
    g_l, g_v = predecir_partido(local, visitante)
    if g_l > g_v:
        return local, f"{g_l} - {g_v}"
    elif g_v > g_l:
        return visitante, f"{g_l} - {g_v}"
    else:
        # Desempate seguro por elo (en minúsculas)
        elo_local = data[local]['elo'] if local in data else 1500
        elo_visit = data[visitante]['elo'] if visitante in data else 1500
        ganador = local if elo_local > elo_visit else visitante
        return ganador, f"{g_l} - {g_v} (Pen.)"

# --- INTERFAZ DE USUARIO (UI) ---
st.title("🏆 Simulador Inteligente - Mundial 2026")
st.markdown("Predicciones automatizadas usando *Distribución de Poisson* y *Ranking Elo*.")

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
                    ganador_e = equipo_a if data[equipo_a]['elo'] > data[equipo_b]['elo'] else equipo_b
                    st.info(f"🤝 **Empate en los 90'.** Por balance de Ranking Elo, avanza en penales: **{ganador_e}**")

    # ---------------------------------------------------------
    # PESTAÑA 2: LLAVES DINÁMICAS
    # ---------------------------------------------------------
    with tab2:
        st.subheader("Simulación del Cuadro Final")
        st.write("El sistema toma automáticamente las 32 mejores selecciones de tu archivo de datos para armar los cruces.")
        
        mejores_32 = list(data.keys())[:32]
        llaves_16avos = []
        for i in range(16):
            llaves_16avos.append((mejores_32[i], mejores_32[31 - i]))
        
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
else:
    st.warning("La base de datos está vacía o el formato del archivo 'equipos.csv' es incorrecto.")
