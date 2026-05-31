
# Mundial 2026 - Advanced Simulator
# Features:
# - 12 grupos de 4
# - Sorteo por bombos (basado en Elo)
# - Poisson + Elo + ventaja anfitrión
# - Desempates por puntos, DG y GF
# - Mejores terceros
# - Bracket de 32
# - Monte Carlo configurable
# - Probabilidades de campeón/finalista/semi/cuartos
# - Visualización en Streamlit

import streamlit as st
import pandas as pd
import numpy as np
from collections import defaultdict

HOSTS = {"Estados Unidos", "México", "Canadá"}

@st.cache_data
def load_data():
    return pd.read_csv("equipos.csv")

def expected_goals(t1, t2):
    home_adv = 1.08 if t1["pais"] in HOSTS else 1.0
    elo_adj = 1 + ((t1["elo"] - t2["elo"]) / 4000)
    return max(0.1, 1.35 * t1["ataque"] * t2["defensa"] * elo_adj * home_adv)

def match(t1, t2):
    g1 = np.random.poisson(expected_goals(t1, t2))
    g2 = np.random.poisson(expected_goals(t2, t1))
    return g1, g2

def create_groups(df):
    df = df.sort_values("elo", ascending=False).reset_index(drop=True)
    pots = [df.iloc[i*12:(i+1)*12].sample(frac=1) for i in range(4)]

    groups = [[] for _ in range(12)]
    for pot in pots:
        for i, (_, row) in enumerate(pot.iterrows()):
            groups[i].append(row)

    return [pd.DataFrame(g) for g in groups]

def group_table(group):
    teams = list(group["pais"])
    stats = {t:[0,0,0] for t in teams}

    for i in range(4):
        for j in range(i+1,4):
            a = group.iloc[i]
            b = group.iloc[j]
            ga,gb = match(a,b)

            stats[a["pais"]][1] += ga-gb
            stats[b["pais"]][1] += gb-ga
            stats[a["pais"]][2] += ga
            stats[b["pais"]][2] += gb

            if ga>gb:
                stats[a["pais"]][0]+=3
            elif gb>ga:
                stats[b["pais"]][0]+=3
            else:
                stats[a["pais"]][0]+=1
                stats[b["pais"]][0]+=1

    rows = [[k,*v] for k,v in stats.items()]
    return pd.DataFrame(rows,columns=["Equipo","Pts","DG","GF"]).sort_values(
        ["Pts","DG","GF"], ascending=False
    )

def knockout(team_a, team_b, df):
    a = df[df.pais==team_a].iloc[0]
    b = df[df.pais==team_b].iloc[0]

    ga,gb = match(a,b)

    if ga==gb:
        return team_a if a["elo"]>=b["elo"] else team_b
    return team_a if ga>gb else team_b

def simulate_tournament(df):
    groups = create_groups(df)

    qualified = []
    thirds = []

    for g in groups:
        t = group_table(g)
        qualified.extend(t.head(2)["Equipo"].tolist())
        thirds.append(t.iloc[2])

    thirds = pd.DataFrame(thirds)
    qualified.extend(
        thirds.sort_values(["Pts","DG","GF"], ascending=False)
        .head(8)["Equipo"].tolist()
    )

    round_ = qualified[:]

    history = {32: round_[:]}

    while len(round_) > 1:
        nxt = []
        for i in range(0,len(round_),2):
            nxt.append(knockout(round_[i], round_[i+1], df))
        round_ = nxt
        history[len(round_)] = round_[:]

    champion = round_[0]
    return champion, history

st.title("🏆 Mundial 2026 Advanced Simulator")

df = load_data()

runs = st.sidebar.slider("Simulaciones Monte Carlo",100,10000,1000,100)

if st.button("Ejecutar Monte Carlo"):
    champ = defaultdict(int)
    finalist = defaultdict(int)
    semi = defaultdict(int)
    quarter = defaultdict(int)

    for _ in range(runs):
        c,h = simulate_tournament(df)

        champ[c]+=1

        if 2 in h:
            for x in h[2]:
                finalist[x]+=1

        if 4 in h:
            for x in h[4]:
                semi[x]+=1

        if 8 in h:
            for x in h[8]:
                quarter[x]+=1

    result = pd.DataFrame({
        "Equipo": list(champ.keys()),
        "Campeón %":[100*v/runs for v in champ.values()],
        "Finalista %":[100*finalist[k]/runs for k in champ.keys()],
        "Semifinal %":[100*semi[k]/runs for k in champ.keys()],
        "Cuartos %":[100*quarter[k]/runs for k in champ.keys()]
    }).sort_values("Campeón %", ascending=False)

    st.dataframe(result, use_container_width=True)
    st.bar_chart(result.set_index("Equipo")["Campeón %"])
