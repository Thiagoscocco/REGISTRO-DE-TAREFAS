import streamlit as st

from ui.utils import formatar_tempo_padrao


def _intervalos_checkpoints(tempos):
    if len(tempos) < 2:
        return []
    return [max(0.0, tempos[i] - tempos[i - 1]) for i in range(1, len(tempos))]


def _media_intervalos(tempos):
    intervalos = _intervalos_checkpoints(tempos)
    if not intervalos:
        return None
    return sum(intervalos) / len(intervalos)


def _formatar_hhmmss(segundos):
    total = int(max(0, float(segundos or 0)))
    horas = total // 3600
    minutos = (total % 3600) // 60
    seg = total % 60
    return f"{horas:02d}:{minutos:02d}:{seg:02d}"


def _tempo_ate_concluir(tempos, media_segundos, alvo_total, tempo_atual):
    if media_segundos is None:
        return None

    concluidas = len(tempos)
    restantes = max(0, int(alvo_total) - concluidas)
    if restantes == 0:
        return 0.0

    desde_ultimo = max(0.0, float(tempo_atual) - float(tempos[-1]))
    proximo_em = max(0.0, float(media_segundos) - desde_ultimo)
    return proximo_em + max(0, restantes - 1) * float(media_segundos)


def _abrir_detalhes_tarefa():
    st.session_state.detalhes_tarefa_aberto = True


def _fechar_detalhes_tarefa():
    st.session_state.detalhes_tarefa_aberto = False


def _abrir_checkpoints():
    st.session_state.checkpoints_aberto = True


def _fechar_checkpoints():
    st.session_state.checkpoints_aberto = False


def _divisao_pertence_objetivo(divisao, objetivo_id):
    if objetivo_id is None:
        return False
    objetivos_ids = divisao.get("objetivo_ids")
    if objetivos_ids:
        return int(objetivo_id) in [int(item) for item in objetivos_ids]
    return divisao.get("objetivo_id") == objetivo_id


def render_cronometro_tab(
    objetivos,
    divisoes,
    cronometro,
    tarefa_ativa_titulo,
    tarefa_ativa_divisao_id,
    label_divisao_fn,
    on_iniciar,
    on_pausar,
    on_recomecar,
    on_parar_salvar,
    on_cancelar,
    on_remover_tempo,
    on_registrar_checkpoint,
):
    if "detalhes_tarefa_aberto" not in st.session_state:
        st.session_state.detalhes_tarefa_aberto = False
    if "checkpoints_aberto" not in st.session_state:
        st.session_state.checkpoints_aberto = False

    objetivo_ids = [o["id"] for o in objetivos]
    if objetivo_ids:
        objetivo_id_salvo = st.session_state.get("cronometro_objetivo_id")
        if objetivo_id_salvo not in objetivo_ids:
            st.session_state.cronometro_objetivo_id = objetivo_ids[0]
    else:
        st.session_state.cronometro_objetivo_id = None

    objetivo_id_atual = st.session_state.get("cronometro_objetivo_id")
    divisoes_do_objetivo = [
        d for d in divisoes if _divisao_pertence_objetivo(d, objetivo_id_atual)
    ]

    divisao_ids = [d["id"] for d in divisoes_do_objetivo]
    divisao_id_salvo = st.session_state.get("cronometro_divisao_id")
    if divisao_ids:
        if divisao_id_salvo not in divisao_ids:
            st.session_state.cronometro_divisao_id = divisao_ids[0]
    else:
        st.session_state.cronometro_divisao_id = None

    divisao_selecionada = st.session_state.get("cronometro_divisao_id")
    titulo_digitado = (st.session_state.get("input_titulo_tarefa") or "").strip()
    titulo_exibicao = tarefa_ativa_titulo or titulo_digitado or "Cronometro de tarefa"

    st.subheader(titulo_exibicao)
    st.markdown(f"## {formatar_tempo_padrao(cronometro.tempo_total())}")
    tarefa_ativa = tarefa_ativa_titulo is not None
    checkpoints_ativado = st.session_state.get("checkpoints_ativado", False)
    tempos = st.session_state.get("checkpoint_tempos", [])
    media_segundos = _media_intervalos(tempos)
    alvo_total = int(st.session_state.get("checkpoint_estimativa_total", 1))
    tempo_ate_concluir = _tempo_ate_concluir(
        tempos=tempos,
        media_segundos=media_segundos,
        alvo_total=alvo_total,
        tempo_atual=cronometro.tempo_total(),
    )

    if checkpoints_ativado and tarefa_ativa:
        if media_segundos is not None:
            st.caption(
                "Tempo medio entre checkpoints: "
                f"{_formatar_hhmmss(media_segundos)}"
            )
        else:
            st.caption("Tempo medio entre checkpoints: aguardando 2 checkpoints.")

        if tempo_ate_concluir is not None:
            st.caption(f"Tempo ate concluir: {_formatar_hhmmss(tempo_ate_concluir)}")
        else:
            st.caption("Tempo ate concluir: aguardando 2 checkpoints.")

    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)

    if not objetivos:
        st.info("Crie ao menos um objetivo e uma divisao de trabalho para iniciar tarefas.")
        if cronometro.rodando() or cronometro.tempo_total() > 0:
            st.button(
                "Descartar tarefa",
                on_click=on_cancelar,
                use_container_width=True,
            )
        return

    if not tarefa_ativa:
        st.button(
            "Iniciar tarefa",
            on_click=on_iniciar,
            args=(divisao_selecionada, st.session_state.get("input_titulo_tarefa", "")),
            type="primary",
            disabled=divisao_selecionada is None,
            use_container_width=True,
        )
    else:
        col1, col2, col3 = st.columns(3)
        if cronometro.rodando():
            col1.button(
                "Pausar tarefa",
                on_click=on_pausar,
                use_container_width=True,
            )
        else:
            col1.button(
                "Recomecar tarefa",
                on_click=on_recomecar,
                use_container_width=True,
            )

        col2.button(
            "Parar e salvar",
            on_click=on_parar_salvar,
            args=(divisoes,),
            type="primary",
            use_container_width=True,
        )
        col3.button(
            "Descartar tarefa",
            on_click=on_cancelar,
            use_container_width=True,
        )

    if checkpoints_ativado and tarefa_ativa:
        st.markdown(
            """
            <style>
            div.st-key-btn_marcar_checkpoint button {
                background-color: #3B82F6 !important;
                color: #F8FAFC !important;
                border: 1px solid #3B82F6 !important;
            }
            div.st-key-btn_marcar_checkpoint button:hover {
                background-color: #2563EB !important;
                border: 1px solid #2563EB !important;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
        st.button(
            "Marcar checkpoint",
            key="btn_marcar_checkpoint",
            on_click=on_registrar_checkpoint,
            disabled=False,
            use_container_width=True,
        )

    with st.expander(
        "Detalhes da Tarefa",
        expanded=st.session_state.get("detalhes_tarefa_aberto", False),
    ):
        col_sp, col_close = st.columns([6, 1])
        col_close.button(
            "Fechar",
            key="fechar_detalhes_tarefa_btn",
            on_click=_fechar_detalhes_tarefa,
            use_container_width=True,
        )
        col_obj, col_div = st.columns(2)
        mapa_objetivos = {o["id"]: o["nome"] for o in objetivos}

        col_obj.selectbox(
            "Objetivo",
            options=objetivo_ids,
            key="cronometro_objetivo_id",
            format_func=lambda item: mapa_objetivos[item],
            disabled=tarefa_ativa,
            on_change=_abrir_detalhes_tarefa,
        )

        objetivo_atual = st.session_state.get("cronometro_objetivo_id")
        divisoes_filtradas = [
            d for d in divisoes if _divisao_pertence_objetivo(d, objetivo_atual)
        ]
        divisao_options = [d["id"] for d in divisoes_filtradas]
        mapa_filtrado = {d["id"]: d["nome"] for d in divisoes_filtradas}

        if st.session_state.get("cronometro_divisao_id") not in divisao_options:
            st.session_state.cronometro_divisao_id = (
                divisao_options[0] if divisao_options else None
            )

        col_div.selectbox(
            "Divisao de trabalho",
            options=divisao_options if divisao_options else [None],
            key="cronometro_divisao_id",
            format_func=lambda item: mapa_filtrado.get(item, "Sem divisao neste objetivo"),
            disabled=tarefa_ativa or not divisao_options,
            on_change=_abrir_detalhes_tarefa,
        )

        st.text_input(
            "Titulo da tarefa",
            key="input_titulo_tarefa",
            disabled=tarefa_ativa,
            placeholder="Ex: Edicao de Front End",
            on_change=_abrir_detalhes_tarefa,
        )

        st.markdown("#### Remover periodo de tempo")
        rm_h, rm_m, rm_s = st.columns(3)
        rm_h.number_input(
            "Horas",
            min_value=0,
            step=1,
            key="remover_periodo_horas",
            on_change=_abrir_detalhes_tarefa,
        )
        rm_m.number_input(
            "Minutos",
            min_value=0,
            step=1,
            key="remover_periodo_minutos",
            on_change=_abrir_detalhes_tarefa,
        )
        rm_s.number_input(
            "Segundos",
            min_value=0,
            step=1,
            key="remover_periodo_segundos",
            on_change=_abrir_detalhes_tarefa,
        )

        total_remover = (
            int(st.session_state.get("remover_periodo_horas", 0)) * 3600
            + int(st.session_state.get("remover_periodo_minutos", 0)) * 60
            + int(st.session_state.get("remover_periodo_segundos", 0))
        )
        if st.button("Remover periodo", key="remover_periodo_btn", use_container_width=True):
            _abrir_detalhes_tarefa()
            on_remover_tempo(total_remover)
            st.session_state.remover_periodo_horas = 0
            st.session_state.remover_periodo_minutos = 0
            st.session_state.remover_periodo_segundos = 0

        if not divisoes_filtradas:
            st.warning("Esse objetivo ainda nao possui divisao de trabalho.")

    if tarefa_ativa:
        with st.expander(
            "Marcar checkpoints",
            expanded=st.session_state.get("checkpoints_aberto", False),
        ):
            col_sp, col_close = st.columns([6, 1])
            col_close.button(
                "Fechar",
                key="fechar_checkpoints_btn",
                on_click=_fechar_checkpoints,
                use_container_width=True,
            )
            st.checkbox(
                "Ativar modo de marcar checkpoints",
                key="checkpoints_ativado",
                on_change=_abrir_checkpoints,
            )
            st.number_input(
                "Estimativa de conclusao (quantidade de tarefas/checkpoints)",
                min_value=1,
                step=1,
                key="checkpoint_estimativa_total",
                on_change=_abrir_checkpoints,
            )
            st.caption(
                "Os checkpoints nao sao salvos em historico. "
                "Sao usados apenas nesta tarefa para estimativa."
            )
    else:
        st.markdown(
            """
            <div style="opacity:0.55;border:1px solid #334155;border-radius:10px;padding:12px 14px;">
                <div style="font-weight:600;">Marcar checkpoints</div>
                <div style="font-size:0.9rem;margin-top:4px;">Inicie uma tarefa para habilitar esta secao.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
