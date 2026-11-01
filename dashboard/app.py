"""Dashboard MotoGP (Streamlit).

Regras:
- lê somente a camada marts (via motogp.dashboard_data);
- não faz nenhum cálculo: todo número já vem pronto do SQL.
  A tela apenas filtra linhas (década, top N) e desenha.

Uso: uv run streamlit run dashboard/app.py
"""

from contextlib import closing

import altair as alt
import streamlit as st

from motogp.config import get_settings
from motogp.dashboard_data import connect_marts, load_marts

st.set_page_config(page_title="MotoGP Analytics", page_icon="🏍️", layout="wide")


@st.cache_data
def get_marts():
    with closing(connect_marts(get_settings().warehouse_dir)) as conn:
        return load_marts(conn)


def show_chart(chart, target=st):
    """Desenha o gráfico ocupando a largura disponível, em qualquer versão do Streamlit."""
    try:
        target.altair_chart(chart, width="stretch")
    except TypeError:  # versões anteriores à 1.46
        target.altair_chart(chart, use_container_width=True)


try:
    marts = get_marts()
except FileNotFoundError as exc:
    st.error(str(exc))
    st.stop()

kpi = marts["kpi_summary"].iloc[0]

# --- Cabeçalho ---------------------------------------------------------------
st.title("🏍️ MotoGP Analytics")
st.caption(
    f"Mundial de Motovelocidade, {int(kpi.first_season)}–{int(kpi.last_season)}. "
    "Fonte: dataset *Moto GP World Championship (1949-2022)*, Kaggle."
)
st.warning(
    "**Limitação da fonte:** algumas temporadas estão incompletas no dataset "
    "(2004, 2014, 2017 e 2022, entre outras). Totais por piloto podem ficar abaixo "
    "dos números oficiais. Detalhes no README do projeto.",
    icon="⚠️",
)

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Vitórias (todas as categorias)", f"{int(kpi.total_race_wins):,}".replace(",", "."))
c2.metric("Vitórias na categoria principal", f"{int(kpi.premier_class_wins):,}".replace(",", "."))
c3.metric("Pilotos vencedores", int(kpi.distinct_winning_riders))
c4.metric("Fabricantes vencedores", int(kpi.distinct_winning_constructors))
c5.metric("Países vencedores", int(kpi.distinct_winning_countries))

st.divider()

# --- 1. Fabricantes por década -------------------------------------------------
st.header("1. Domínio dos fabricantes por década")
st.caption("Categoria principal (500cc/MotoGP). Os 3 fabricantes que mais venceram em cada década.")

cw = marts["constructor_wins_by_decade"]
top3 = cw[cw.rank_in_decade <= 3]
chart = (
    alt.Chart(top3)
    .mark_bar()
    .encode(
        x=alt.X("decade:O", title="Década"),
        y=alt.Y("share_pct:Q", title="% das vitórias da década"),
        color=alt.Color("constructor_name:N", title="Fabricante"),
        xOffset="constructor_name:N",
        tooltip=[
            alt.Tooltip("decade:O", title="Década"),
            alt.Tooltip("constructor_name:N", title="Fabricante"),
            alt.Tooltip("wins:Q", title="Vitórias"),
            alt.Tooltip("share_pct:Q", title="% da década"),
        ],
    )
    .properties(height=380)
)
show_chart(chart)

# --- 2. Domínio do campeão -----------------------------------------------------
st.header("2. Quanto o fabricante campeão dominou a temporada")
st.caption("Percentual das corridas da categoria principal vencidas pelo campeão de construtores.")

cd = marts["champion_dominance"]
chart = (
    alt.Chart(cd)
    .mark_line(point=True)
    .encode(
        x=alt.X("season:Q", title="Temporada", axis=alt.Axis(format="d")),
        y=alt.Y("champion_win_pct:Q", title="% de vitórias do campeão", scale=alt.Scale(domain=[0, 100])),
        tooltip=[
            alt.Tooltip("season:O", title="Temporada"),
            alt.Tooltip("champion_constructor:N", title="Campeão"),
            alt.Tooltip("champion_wins:Q", title="Vitórias"),
            alt.Tooltip("season_races:Q", title="Corridas"),
            alt.Tooltip("champion_win_pct:Q", title="%"),
        ],
    )
    .properties(height=320)
)
show_chart(chart)

# --- 3. Maiores vencedores ---------------------------------------------------
st.header("3. Maiores vencedores da categoria principal")
top_n = st.slider("Quantas posições mostrar", min_value=5, max_value=30, value=15)

tr = marts["top_riders_premier"]
tr_top = tr[tr.rank_position <= top_n]
chart = (
    alt.Chart(tr_top)
    .mark_bar()
    .encode(
        x=alt.X("wins:Q", title="Vitórias"),
        y=alt.Y("rider_name:N", title=None, sort="-x"),
        color=alt.Color("country_code:N", title="País"),
        tooltip=[
            alt.Tooltip("rank_position:Q", title="Posição"),
            alt.Tooltip("rider_name:N", title="Piloto"),
            alt.Tooltip("country_code:N", title="País"),
            alt.Tooltip("wins:Q", title="Vitórias"),
            alt.Tooltip("winning_seasons:Q", title="Temporadas com vitória"),
            alt.Tooltip("first_win_season:O", title="Primeira vitória"),
            alt.Tooltip("last_win_season:O", title="Última vitória"),
        ],
    )
    .properties(height=max(300, 24 * len(tr_top)))
)
show_chart(chart)

# --- 4. Países por década ----------------------------------------------------
st.header("4. Países que mais venceram")
wc = marts["wins_by_country_decade"]
decades = sorted(int(d) for d in wc.decade.unique())
decade = st.select_slider("Década", options=decades, value=decades[-1])

wc_decade = wc[(wc.decade == decade) & (wc.rank_in_decade <= 10)]
col_chart, col_table = st.columns([3, 2])
chart = (
    alt.Chart(wc_decade)
    .mark_bar()
    .encode(
        x=alt.X("share_pct:Q", title="% das vitórias da década (todas as categorias)"),
        y=alt.Y("country_code:N", title=None, sort="-x"),
        tooltip=[
            alt.Tooltip("country_code:N", title="País"),
            alt.Tooltip("wins:Q", title="Vitórias"),
            alt.Tooltip("premier_class_wins:Q", title="Na categoria principal"),
            alt.Tooltip("share_pct:Q", title="%"),
        ],
    )
)
show_chart(chart, col_chart)
col_table.dataframe(
    wc_decade[["rank_in_decade", "country_code", "wins", "premier_class_wins", "share_pct"]],
    hide_index=True,
    column_config={
        "rank_in_decade": "Posição",
        "country_code": "País",
        "wins": "Vitórias",
        "premier_class_wins": "Categoria principal",
        "share_pct": st.column_config.NumberColumn("% da década", format="%.1f%%"),
    },
)

# --- 5. Pódios de uma só nação -----------------------------------------------
st.header("5. Pódios de uma só nacionalidade")
st.caption("Corridas em que os três pilotos do pódio eram do mesmo país, todas as categorias.")

pl = marts["podium_lockouts_by_nation"]
chart = (
    alt.Chart(pl)
    .mark_bar()
    .encode(
        x=alt.X("decade:O", title="Década"),
        y=alt.Y("lockouts:Q", title="Pódios"),
        color=alt.Color("nation_code:N", title="País"),
        tooltip=[
            alt.Tooltip("decade:O", title="Década"),
            alt.Tooltip("nation_code:N", title="País"),
            alt.Tooltip("lockouts:Q", title="Pódios"),
            alt.Tooltip("premier_class_lockouts:Q", title="Na categoria principal"),
        ],
    )
    .properties(height=340)
)
show_chart(chart)
