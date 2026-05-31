import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
from collections import defaultdict

st.set_page_config(
    page_title="Simulador Mundial 2026",
    page_icon="🏆",
    layout="wide"
)

HOSTS = {"Estados Unidos", "México", "Canadá"}

@st.cache_data
def load_data():

    csv_path = Path(__file__).parent / "equipos.csv"

    if not csv_path.exists():
        st.error(f"No se encontró {csv_path}")
        st.stop()

    df = pd.read_csv(csv_path)

    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
    )

    required = {"pais", "ataque", "defensa", "elo"}

    missing = required - set(df.columns)

    if missing:
        st.error(f"Faltan columnas: {missing}")
        st.stop()

    return df

def expected_goals(team1, team2):

    host_bonus = (
        1.08
        if team1["pais"] in HOSTS
        else 1.0
    )

    elo_factor = (
        1 + (team1["elo"] - team2["elo"]) / 4000
    )

    xg = (
        1.35
        * team1["ataque"]
        * team2["defensa"]
        * elo_factor
        * host_bonus
    )

    return max(xg, 0.1)

def play_match(team1, team2):

    g1 = np.random.poisson(
        expected_goals(team1, team2)
    )

    g2 = np.random.poisson(
        expected_goals(team2, team1)
    )

    return g1, g2

def simulate_group(group):

    teams = list(group["pais"])

    table = {
        t: {"pts":0,"gf":0,"ga":0}
        for t in teams
    }

    for i in range(len(teams)):
        for j in range(i + 1, len(teams)):

            t1 = group[group["pais"] == teams[i]].iloc[0]
            t2 = group[group["pais"] == teams[j]].iloc[0]

            g1, g2 = play_match(t1, t2)

            table[teams[i]]["gf"] += g1
            table[teams[i]]["ga"] += g2

            table[teams[j]]["gf"] += g2
            table[teams[j]]["ga"] += g1

            if g1 > g2:
                table[teams[i]]["pts"] += 3
            elif g2 > g1:
                table[teams[j]]["pts"] += 3
            else:
                table[teams[i]]["pts"] += 1
                table[teams[j]]["pts"] += 1

    rows = []

    for team, stats in table.items():
        rows.append([
            team,
            stats["pts"],
            stats["gf"] - stats["ga"],
            stats["gf"]
        ])

    return pd.DataFrame(
        rows,
        columns=["Equipo","Pts","DG","GF"]
    ).sort_values(
        ["Pts","DG","GF"],
        ascending=False
    )

def knockout(team_a, team_b, df):

    a = df[df["pais"] == team_a].iloc[0]
    b = df[df["pais"] == team_b].iloc[0]

    g1, g2 = play_match(a, b)

    if g1 > g2:
        return team_a

    if g2 > g1:
        return team_b

    return (
        team_a
        if a["elo"] >= b["elo"]
        else team_b
    )

def create_groups(df):

    shuffled = df.sample(
        frac=1
    ).reset_index(drop=True)

    groups = []

    for i in range(12):
        groups.append(
            shuffled.iloc[i*4:(i+1)*4]
        )

    return groups

def simulate_tournament(df):

    groups = create_groups(df)

    qualified = []
    third_places = []

    for group in groups:

        table = simulate_group(group)

        qualified.extend(
            table.head(2)["Equipo"].tolist()
        )

        third_places.append(
            table.iloc[2]
        )

    thirds = pd.DataFrame(third_places)

    best_thirds = thirds.sort_values(
        ["Pts","DG","GF"],
        ascending=False
    ).head(8)

    qualified.extend(
        best_thirds["Equipo"].tolist()
    )

    round32 = qualified.copy()

    quarterfinalists = []
    semifinalists = []
    finalists = []

    while len(round32) > 1:

        next_round = []

        for i in range(0, len(round32), 2):

            winner = knockout(
                round32[i],
                round32[i+1],
                df
            )

            next_round.append(winner)

        if len(next_round) == 8:
            quarterfinalists = next_round.copy()

        if len(next_round) == 4:
            semifinalists = next_round.copy()

        if len(next_round) == 2:
            finalists = next_round.copy()

        round32 = next_round

    champion = round32[0]

    return (
        champion,
        finalists,
        semifinalists,
        quarterfinalists
    )

st.title("🏆 Simulador Mundial 2026")

df = load_data()

runs = st.sidebar.slider(
    "Cantidad de simulaciones",
    100,
    5000,
    1000,
    100
)

if st.button("Ejecutar simulación Monte Carlo"):

    champions = defaultdict(int)
    finalists = defaultdict(int)
    semis = defaultdict(int)
    quarters = defaultdict(int)

    progress = st.progress(0)

    for i in range(runs):

        (
            champion,
            final,
            semi,
            quarter
        ) = simulate_tournament(df)

        champions[champion] += 1

        for t in final:
            finalists[t] += 1

        for t in semi:
            semis[t] += 1

        for t in quarter:
            quarters[t] += 1

        progress.progress(
            (i + 1) / runs
        )

    result = pd.DataFrame({
        "Equipo": list(champions.keys()),
        "Campeón %": [
            champions[t] * 100 / runs
            for t in champions
        ],
        "Finalista %": [
            finalists[t] * 100 / runs
            for t in champions
        ],
        "Semifinal %": [
            semis[t] * 100 / runs
            for t in champions
        ],
        "Cuartos %": [
            quarters[t] * 100 / runs
            for t in champions
        ]
    })

    result = result.sort_values(
        "Campeón %",
        ascending=False
    )

    st.subheader("Probabilidades")

    st.dataframe(
        result,
        use_container_width=True
    )

    st.bar_chart(
        result.set_index("Equipo")["Campeón %"]
    )
