import streamlit as st

from ui.utils import formatar_tempo_padrao


def _cor_texto_para_fundo(cor_hex):
    try:
        valor = cor_hex.lstrip("#")
        r = int(valor[0:2], 16)
        g = int(valor[2:4], 16)
        b = int(valor[4:6], 16)
    except Exception:
        return "#F8FAFC"

    luminancia = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    return "#0B1220" if luminancia >= 0.62 else "#F8FAFC"


def _valor_por_periodo(total, semana, hoje, periodo):
    if periodo == "Tempo na semana":
        return semana
    if periodo == "Tempo hoje":
        return hoje
    return total


def _cartao_objetivo(nome, cor):
    cor_texto = _cor_texto_para_fundo(cor)
    st.markdown(
        (
            f"<div style='background:{cor};"
            f"padding:10px 14px;border-radius:10px;color:{cor_texto};"
            "font-weight:700;letter-spacing:0.3px;'>"
            f"{nome}</div>"
        ),
        unsafe_allow_html=True,
    )


def _divisao_vinculada_ao_objetivo(divisao, objetivo_id):
    objetivos_ids = divisao.get("objetivo_ids")
    if objetivos_ids:
        return int(objetivo_id) in [int(item) for item in objetivos_ids]
    return divisao.get("objetivo_id") == objetivo_id


def render_objetivos_tab(
    objetivos,
    divisoes,
    resumo_objetivo_fn,
    resumo_divisao_fn,
    on_criar_objetivo,
    on_apagar_objetivo,
    on_randomizar_cores,
):
    if st.session_state.get("_objetivos_tab_renderizado", False):
        return
    st.session_state._objetivos_tab_renderizado = True

    st.subheader("Objetivos")

    if "objetivo_expandido_id" not in st.session_state:
        st.session_state.objetivo_expandido_id = None
    if "objetivos_periodo" not in st.session_state:
        st.session_state.objetivos_periodo = "Tempo total"
    with st.popover("Adicionar novo objetivo"):
        nome_objetivo = st.text_input("Nome do objetivo", key="novo_objetivo_nome")
        if st.button("Salvar objetivo", key="salvar_novo_objetivo"):
            on_criar_objetivo(nome_objetivo)

    if not objetivos:
        st.info("Nenhum objetivo criado ainda.")
    else:
        periodo = st.session_state.objetivos_periodo

        for objetivo in objetivos:
            objetivo_id = objetivo["id"]
            expandido = st.session_state.objetivo_expandido_id == objetivo_id
            total_obj, semana_obj, hoje_obj = resumo_objetivo_fn(objetivo_id)
            tempo_obj = _valor_por_periodo(total_obj, semana_obj, hoje_obj, periodo)

            c_nome, c_tempo, c_toggle = st.columns([8, 3, 1], gap="small")
            with c_nome:
                _cartao_objetivo(objetivo["nome"], objetivo.get("cor") or "#334155")
            with c_tempo:
                st.markdown(
                    (
                        "<div style='text-align:right;padding-top:10px;font-weight:700;'>"
                        f"{formatar_tempo_padrao(tempo_obj)}"
                        "</div>"
                    ),
                    unsafe_allow_html=True,
                )
            with c_toggle:
                if st.button("v" if expandido else ">", key=f"toggle_obj_{objetivo_id}"):
                    st.session_state.objetivo_expandido_id = (
                        None if expandido else objetivo_id
                    )
                    st.rerun()

            if not expandido:
                st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
                continue

            divisoes_objetivo = [
                d for d in divisoes if _divisao_vinculada_ao_objetivo(d, objetivo_id)
            ]
            if not divisoes_objetivo:
                st.caption("Sem divisoes vinculadas.")
            else:
                for divisao in divisoes_objetivo:
                    total_d, semana_d, hoje_d = resumo_divisao_fn(divisao["id"])
                    tempo_div = _valor_por_periodo(total_d, semana_d, hoje_d, periodo)
                    col_nome, col_tempo = st.columns([8, 4], gap="small")
                    col_nome.write(divisao["nome"])
                    col_tempo.markdown(
                        (
                            "<div style='text-align:right;'>"
                            f"{formatar_tempo_padrao(tempo_div)}"
                            "</div>"
                        ),
                        unsafe_allow_html=True,
                    )

            st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)

    st.divider()
    with st.expander("Configuracoes de Objetivos", expanded=False):
        cfg_left, cfg_right = st.columns([1, 1], gap="large")
        cfg_left.selectbox(
            "Visualizar tempo por",
            options=["Tempo total", "Tempo na semana", "Tempo hoje"],
            key="objetivos_periodo",
        )
        if cfg_right.button("Alterar cores da paleta", use_container_width=True):
            on_randomizar_cores()

        if objetivos:
            mapa_objetivos = {o["id"]: o["nome"] for o in objetivos}
            del_left, del_right = st.columns([3, 1], gap="small")
            del_left.selectbox(
                "Apagar objetivo",
                options=[o["id"] for o in objetivos],
                format_func=lambda item: mapa_objetivos[item],
                key="objetivo_para_apagar",
            )
            del_right.markdown("<br>", unsafe_allow_html=True)
            if del_right.button(
                "Apagar",
                type="primary",
                use_container_width=True,
                key="apagar_objetivo_btn",
            ):
                on_apagar_objetivo(st.session_state.objetivo_para_apagar)
