import plotly.express as px
import streamlit as st


_PALETA_DIVISOES = [
    "#5B8D8D",
    "#CDB981",
    "#B45E5E",
    "#7A8D9E",
    "#4A4A4A",
    "#6E665B",
    "#6A9998",
    "#77A5A3",
    "#86B2AE",
    "#A99765",
    "#B6A572",
    "#C1B07C",
    "#9F5555",
    "#AA5A5A",
    "#C36A6A",
    "#6D8194",
    "#637789",
    "#8799A9",
    "#555555",
    "#626262",
    "#6F6F6F",
    "#7A7266",
    "#867D70",
    "#91887A",
]


def _render_grafico_pizza(titulo, dados, usar_cores_dados=False):
    if not dados:
        st.info("Sem dados para este periodo.")
        return

    nomes = [item["nome"] for item in dados]
    valores = [item["valor"] for item in dados]
    kwargs = {}

    if usar_cores_dados:
        mapa_cores = {
            item["nome"]: item.get("cor")
            for item in dados
            if item.get("cor")
        }
        kwargs["color"] = nomes
        if mapa_cores:
            kwargs["color_discrete_map"] = mapa_cores
    else:
        kwargs["color"] = nomes
        kwargs["color_discrete_sequence"] = _PALETA_DIVISOES

    fig = px.pie(
        values=valores,
        names=nomes,
        title=titulo,
        hole=0.4,
        **kwargs,
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    fig.update_layout(margin=dict(l=10, r=10, t=60, b=10))
    st.plotly_chart(fig, use_container_width=True)


def render_estatisticas_tab(dados_objetivos_por_periodo_fn, dados_divisoes_por_periodo_fn):
    st.subheader("Estatisticas")

    periodo = st.selectbox(
        "Periodo",
        options=["Tempo total", "Tempo semanal", "Tempo hoje"],
        index=0,
        key="estatisticas_periodo",
    )

    st.markdown("### Objetivos")
    dados_objetivos = dados_objetivos_por_periodo_fn(periodo)
    _render_grafico_pizza(f"Objetivos - {periodo}", dados_objetivos, usar_cores_dados=True)

    st.markdown("### Divisoes de Trabalho")
    dados_divisoes = dados_divisoes_por_periodo_fn(periodo)
    _render_grafico_pizza(f"Divisoes de Trabalho - {periodo}", dados_divisoes)
