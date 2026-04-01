import streamlit as st

from ui.utils import formatar_data, formatar_tempo_padrao, valor_por_periodo


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


def _cartao_divisao(nome, cor):
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


def _agrupar_divisoes_por_objetivo(divisoes):
    grupos = {}
    for divisao in divisoes:
        objetivo_id = divisao.get("objetivo_id")
        if objetivo_id not in grupos:
            grupos[objetivo_id] = {
                "objetivo_id": objetivo_id,
                "objetivo_nome": divisao.get("objetivo_nome") or "Sem objetivo",
                "objetivo_cor": divisao.get("objetivo_cor") or "#334155",
                "ultima_atualizacao": "",
                "frequencia": 0,
                "divisoes": [],
            }

        grupo = grupos[objetivo_id]
        grupo["divisoes"].append(divisao)

        ultima = divisao.get("ultima_atualizacao") or ""
        if ultima > grupo["ultima_atualizacao"]:
            grupo["ultima_atualizacao"] = ultima

        grupo["frequencia"] += int(divisao.get("total_tarefas") or 0)

    grupos_ordenados = sorted(
        grupos.values(),
        key=lambda item: (
            item["ultima_atualizacao"],
            item["frequencia"],
            item["objetivo_nome"].lower(),
        ),
        reverse=True,
    )

    for grupo in grupos_ordenados:
        grupo["divisoes"] = sorted(
            grupo["divisoes"],
            key=lambda divisao: (
                divisao.get("ultima_atualizacao") or "",
                divisao.get("nome", "").lower(),
            ),
            reverse=True,
        )

    return grupos_ordenados


def render_divisoes_tab(
    objetivos,
    divisoes,
    resumo_divisao_fn,
    listar_tarefas_da_divisao_fn,
    on_criar_divisao,
    on_apagar_divisao,
):
    st.subheader("Divisoes de Trabalho")

    if "divisao_expandida_id" not in st.session_state:
        st.session_state.divisao_expandida_id = None
    if "divisoes_periodo" not in st.session_state:
        st.session_state.divisoes_periodo = "Tempo total"

    with st.popover("Adicionar nova divisao de trabalho"):
        if not objetivos:
            st.info("Crie um objetivo antes de adicionar divisoes.")
        else:
            opcoes_objetivo = [o["id"] for o in objetivos]
            mapa_objetivo = {o["id"]: o["nome"] for o in objetivos}
            objetivo_id = st.selectbox(
                "Objetivo",
                options=opcoes_objetivo,
                format_func=lambda item: mapa_objetivo[item],
                key="nova_divisao_objetivo_id",
            )
            nome_divisao = st.text_input("Nome da divisao", key="nova_divisao_nome")
            if st.button("Salvar divisao", key="salvar_nova_divisao"):
                on_criar_divisao(objetivo_id, nome_divisao)

    if not divisoes:
        st.info("Nenhuma divisao criada ainda.")
    else:
        periodo = st.session_state.divisoes_periodo
        grupos = _agrupar_divisoes_por_objetivo(divisoes)

        for grupo in grupos:
            st.markdown(f"#### {grupo['objetivo_nome']}")
            st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)

            for divisao in grupo["divisoes"]:
                divisao_id = divisao["id"]
                expandido = st.session_state.divisao_expandida_id == divisao_id
                total, semana, hoje = resumo_divisao_fn(divisao_id)
                tempo_div = valor_por_periodo(total, semana, hoje, periodo)

                c_nome, c_tempo, c_toggle = st.columns([8, 3, 1], gap="small")
                with c_nome:
                    _cartao_divisao(divisao["nome"], divisao.get("objetivo_cor") or "#334155")
                with c_tempo:
                    st.markdown(
                        (
                            "<div style='text-align:right;padding-top:10px;font-weight:700;'>"
                            f"{formatar_tempo_padrao(tempo_div)}"
                            "</div>"
                        ),
                        unsafe_allow_html=True,
                    )
                with c_toggle:
                    if st.button("v" if expandido else ">", key=f"toggle_div_{divisao_id}"):
                        st.session_state.divisao_expandida_id = (
                            None if expandido else divisao_id
                        )
                        st.rerun()

                if not expandido:
                    st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
                    continue

                tarefas = listar_tarefas_da_divisao_fn(divisao_id)
                if not tarefas:
                    st.caption("Sem atividades registradas.")
                else:
                    for tarefa in tarefas:
                        t1, t2, t3 = st.columns([6, 3, 3], gap="small")
                        t1.write(tarefa["titulo"])
                        t2.markdown(
                            (
                                "<div style='text-align:right;'>"
                                f"{formatar_tempo_padrao(tarefa['duracao_segundos'])}"
                                "</div>"
                            ),
                            unsafe_allow_html=True,
                        )
                        t3.markdown(
                            (
                                "<div style='text-align:right;'>"
                                f"{formatar_data(tarefa['fim_em'] or tarefa['criado_em'])}"
                                "</div>"
                            ),
                            unsafe_allow_html=True,
                        )

                st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)

            st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)

    st.divider()
    with st.expander("Configuracoes de Divisoes", expanded=False):
        cfg_left, cfg_right = st.columns([1, 1], gap="large")
        cfg_left.selectbox(
            "Visualizar tempo por",
            options=["Tempo total", "Tempo na semana", "Tempo hoje"],
            key="divisoes_periodo",
        )
        cfg_right.markdown("<br>", unsafe_allow_html=True)

        if divisoes:
            divisoes_cfg = []
            for grupo in _agrupar_divisoes_por_objetivo(divisoes):
                divisoes_cfg.extend(grupo["divisoes"])
            mapa_divisoes = {
                d["id"]: f"{d.get('objetivo_nome') or 'Sem objetivo'} / {d['nome']}"
                for d in divisoes_cfg
            }
            del_left, del_right = st.columns([3, 1], gap="small")
            del_left.selectbox(
                "Apagar divisao",
                options=[d["id"] for d in divisoes_cfg],
                format_func=lambda item: mapa_divisoes[item],
                key="divisao_para_apagar",
            )
            del_right.markdown("<br>", unsafe_allow_html=True)
            if del_right.button(
                "Apagar",
                type="primary",
                use_container_width=True,
                key="apagar_divisao_btn",
            ):
                on_apagar_divisao(st.session_state.divisao_para_apagar)
