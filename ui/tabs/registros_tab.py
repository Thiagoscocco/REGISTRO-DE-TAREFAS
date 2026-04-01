import streamlit as st

from ui.utils import formatar_tempo_padrao


def render_registros_tab(objetivos_resumo, divisoes_resumo):
    st.subheader("Registros")

    st.markdown("### Objetivos")
    if not objetivos_resumo:
        st.info("Nenhum objetivo criado ainda.")
    else:
        for objetivo in objetivos_resumo:
            st.markdown(f"#### {objetivo['nome']}")
            col1, col2, col3 = st.columns(3)
            col1.metric("Horas Totais", formatar_tempo_padrao(objetivo["total"]))
            col2.metric("Horas na semana", formatar_tempo_padrao(objetivo["semana"]))
            col3.metric("Horas hoje", formatar_tempo_padrao(objetivo["hoje"]))

    st.divider()
    st.markdown("### Divisoes de Trabalho")
    if not divisoes_resumo:
        st.info("Nenhuma divisao criada ainda.")
        return

    for divisao in divisoes_resumo:
        st.markdown(f"#### {divisao['nome']}")
        col1, col2, col3 = st.columns(3)
        col1.metric("Horas Totais", formatar_tempo_padrao(divisao["total"]))
        col2.metric("Horas na semana", formatar_tempo_padrao(divisao["semana"]))
        col3.metric("Horas hoje", formatar_tempo_padrao(divisao["hoje"]))
