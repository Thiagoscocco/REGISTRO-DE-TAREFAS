import streamlit as st


def render_configuracoes_tab(
    objetivos,
    divisoes,
    on_adicionar_tarefa_manual,
    on_resetar,
):
    st.subheader("Configuracoes")
    st.markdown("### Adicionar tarefa manualmente")

    if not divisoes:
        st.info("Crie uma divisao de trabalho antes de adicionar tarefas.")
    else:
        opcoes_objetivo = [o["id"] for o in objetivos]
        mapa_objetivos = {o["id"]: o["nome"] for o in objetivos}

        with st.form("form_tarefa_manual", clear_on_submit=True):
            objetivo_manual = st.selectbox(
                "Objetivo",
                options=opcoes_objetivo,
                format_func=lambda item: mapa_objetivos[item],
            )

            def _divisao_do_objetivo(divisao, objetivo_id):
                objetivos_ids = divisao.get("objetivo_ids")
                if objetivos_ids:
                    return int(objetivo_id) in [int(item) for item in objetivos_ids]
                return divisao.get("objetivo_id") == objetivo_id

            divisoes_objetivo = [
                d for d in divisoes if _divisao_do_objetivo(d, objetivo_manual)
            ]
            opcoes_divisao = [d["id"] for d in divisoes_objetivo]
            mapa_divisoes = {d["id"]: d["nome"] for d in divisoes_objetivo}

            divisao_manual = st.selectbox(
                "Divisao de trabalho",
                options=opcoes_divisao if opcoes_divisao else [None],
                format_func=lambda item: mapa_divisoes.get(
                    item, "Sem divisao neste objetivo"
                ),
                disabled=not opcoes_divisao,
            )
            titulo_manual = st.text_input("Titulo da tarefa")
            duracao_manual = st.text_input(
                "Duracao (HH:MM:SS)",
                key="input_duracao_manual",
            )
            data_manual = st.date_input("Data da tarefa")
            hora_manual = st.time_input("Horario de termino")
            enviar_manual = st.form_submit_button(
                "Adicionar tarefa manual",
                disabled=not opcoes_divisao,
            )
            if enviar_manual:
                on_adicionar_tarefa_manual(
                    divisao_manual, titulo_manual, duracao_manual, data_manual, hora_manual
                )

    st.markdown("### Reset geral")
    st.caption("Isso apaga todos os objetivos, todas as divisoes e todas as tarefas salvas.")
    confirmar_reset = st.checkbox("Confirmo que quero apagar tudo")
    if st.button("Apagar todos os dados", type="primary", use_container_width=True):
        on_resetar(confirmar_reset)
