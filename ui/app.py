import time
from datetime import datetime, timedelta
from pathlib import Path

import streamlit as st

from engine.cronometro import Cronometro
from engine.dados_teste import popular_dados_teste, remover_dados_teste
from engine.repositorio import RepositorioDados
from ui.tabs import (
    render_configuracoes_tab,
    render_cronometro_tab,
    render_divisoes_tab,
    render_estatisticas_tab,
    render_objetivos_tab,
)
from ui.utils import (
    label_divisao,
    parse_duracao_hhmmss,
    resumo_periodos_tarefas,
    valor_por_periodo,
)


class App:
    def __init__(self):
        st.set_page_config(page_title="GEST\u00c3O DE TAREFAS", layout="centered")

        if "cronometro" not in st.session_state:
            st.session_state.cronometro = Cronometro()
        if "repo" not in st.session_state:
            st.session_state.repo = RepositorioDados()
        if "tarefa_ativa_titulo" not in st.session_state:
            st.session_state.tarefa_ativa_titulo = None
        if "tarefa_ativa_divisao_id" not in st.session_state:
            st.session_state.tarefa_ativa_divisao_id = None
        if "input_titulo_tarefa" not in st.session_state:
            st.session_state.input_titulo_tarefa = ""
        if "input_duracao_manual" not in st.session_state:
            st.session_state.input_duracao_manual = "00:30:00"
        if "checkpoints_ativado" not in st.session_state:
            st.session_state.checkpoints_ativado = False
        if "checkpoint_tempos" not in st.session_state:
            st.session_state.checkpoint_tempos = []
        if "checkpoint_estimativa_total" not in st.session_state:
            st.session_state.checkpoint_estimativa_total = 1

    @property
    def cronometro(self):
        return st.session_state.cronometro

    @property
    def repo(self):
        return st.session_state.repo

    def _limpar_tarefa_ativa(self):
        st.session_state.tarefa_ativa_titulo = None
        st.session_state.tarefa_ativa_divisao_id = None
        st.session_state.input_titulo_tarefa = ""

    def _limpar_checkpoints(self):
        st.session_state.checkpoint_tempos = []
        st.session_state.checkpoint_estimativa_total = 1
        st.session_state.checkpoints_ativado = False

    def _divisao_por_id(self, divisoes, divisao_id):
        for divisao in divisoes:
            if divisao["id"] == divisao_id:
                return divisao
        return None

    def _iniciar_tarefa(self, divisao_id, titulo):
        if divisao_id is None:
            st.warning("Selecione uma divisao de trabalho.")
            return
        titulo_limpo = (titulo or "").strip()
        if not titulo_limpo:
            st.warning("Informe o titulo da tarefa antes de iniciar.")
            return

        self._limpar_checkpoints()
        st.session_state.tarefa_ativa_divisao_id = int(divisao_id)
        st.session_state.tarefa_ativa_titulo = titulo_limpo
        self.cronometro.iniciar()

    def _pausar_tarefa(self):
        self.cronometro.pausar()

    def _recomecar_tarefa(self):
        self.cronometro.recomecar()

    def _cancelar_tarefa(self):
        self.cronometro.resetar()
        self._limpar_tarefa_ativa()
        self._limpar_checkpoints()

    def _remover_tempo_tarefa(self, segundos):
        if segundos <= 0:
            st.warning("Informe um periodo maior que zero para remover.")
            return

        removido = self.cronometro.remover_tempo(segundos)
        if removido <= 0:
            st.warning("Nao ha tempo suficiente para remover.")
            return

        st.success("Periodo removido do cronometro.")

    def _registrar_checkpoint_tarefa(self):
        if not st.session_state.get("checkpoints_ativado", False):
            st.warning("Ative o modo de checkpoints para registrar.")
            return

        if st.session_state.tarefa_ativa_titulo is None:
            st.warning("Inicie uma tarefa antes de registrar checkpoints.")
            return

        tempo_atual = float(self.cronometro.tempo_total())
        if tempo_atual <= 0:
            st.warning("O cronometro ainda esta zerado.")
            return

        tempos = list(st.session_state.get("checkpoint_tempos", []))
        if tempos and tempo_atual <= float(tempos[-1]):
            st.warning("Aguarde o tempo avancar para registrar o proximo checkpoint.")
            return

        tempos.append(tempo_atual)
        st.session_state.checkpoint_tempos = tempos

    def _parar_e_salvar_tarefa(self, divisoes):
        divisao_id = st.session_state.tarefa_ativa_divisao_id
        titulo = st.session_state.tarefa_ativa_titulo
        if divisao_id is None or not titulo:
            st.warning("Nao existe tarefa ativa para salvar.")
            return

        duracao = self.cronometro.finalizar()
        if duracao <= 0:
            self._limpar_tarefa_ativa()
            self._limpar_checkpoints()
            st.warning("Tempo zerado. Nenhuma tarefa foi salva.")
            return

        divisao = self._divisao_por_id(divisoes, divisao_id)
        if divisao is None:
            self._limpar_tarefa_ativa()
            self._limpar_checkpoints()
            st.error("A divisao selecionada nao existe mais.")
            return

        fim = datetime.now()
        inicio = fim - timedelta(seconds=duracao)
        self.repo.adicionar_tarefa(
            divisao_id=divisao_id,
            titulo=titulo,
            duracao_segundos=duracao,
            inicio_em=inicio.isoformat(timespec="seconds"),
            fim_em=fim.isoformat(timespec="seconds"),
            manual=False,
        )

        self._limpar_tarefa_ativa()
        self._limpar_checkpoints()
        st.success("Tarefa salva com sucesso.")

    def _criar_objetivo(self, nome_objetivo):
        try:
            self.repo.criar_objetivo(nome_objetivo)
            st.success("Objetivo criado.")
            st.rerun()
        except ValueError as exc:
            st.error(str(exc))
        except Exception:
            st.error("Nao foi possivel criar o objetivo. Nome pode ja existir.")

    def _apagar_objetivo(self, objetivo_id):
        divisoes = self.repo.listar_divisoes()
        divisoes_objetivo = [d["id"] for d in divisoes if d["objetivo_id"] == objetivo_id]
        if st.session_state.tarefa_ativa_divisao_id in divisoes_objetivo:
            self.cronometro.resetar()
            self._limpar_tarefa_ativa()
            self._limpar_checkpoints()
        self.repo.remover_objetivo(objetivo_id)
        st.rerun()

    def _randomizar_cores_objetivos(self):
        total = self.repo.randomizar_cores_objetivos()
        if total == 0:
            st.warning("Nao ha objetivos para alterar as cores.")
            return
        st.success("Paleta dos objetivos atualizada.")
        st.rerun()

    def _criar_divisao(self, objetivo_id, nome_divisao):
        try:
            self.repo.criar_divisao(objetivo_id, nome_divisao)
            st.success("Divisao criada.")
            st.rerun()
        except ValueError as exc:
            st.error(str(exc))
        except Exception:
            st.error("Nao foi possivel criar a divisao. Nome pode ja existir.")

    def _apagar_divisao(self, divisao_id):
        if st.session_state.tarefa_ativa_divisao_id == int(divisao_id):
            self.cronometro.resetar()
            self._limpar_tarefa_ativa()
            self._limpar_checkpoints()
        self.repo.remover_divisao(divisao_id)
        st.rerun()

    def _remover_tarefa(self, tarefa_id):
        self.repo.remover_tarefa(tarefa_id)
        st.rerun()

    def _adicionar_tarefa_manual(
        self, divisao_id, titulo, duracao_texto, data_manual, hora_manual
    ):
        try:
            duracao_segundos = parse_duracao_hhmmss(duracao_texto)
            inicio_em, fim_em = self.repo.montar_intervalo_manual(
                data_manual,
                hora_manual,
                duracao_segundos,
            )
            self.repo.adicionar_tarefa(
                divisao_id=divisao_id,
                titulo=titulo,
                duracao_segundos=duracao_segundos,
                inicio_em=inicio_em,
                fim_em=fim_em,
                manual=True,
            )
            st.success("Tarefa manual adicionada.")
            st.rerun()
        except ValueError as exc:
            st.error(str(exc))

    def _resetar_tudo(self, confirmado):
        if not confirmado:
            st.warning("Marque a confirmacao para continuar.")
            return
        self.repo.resetar_tudo()
        self.cronometro.resetar()
        self._limpar_tarefa_ativa()
        self._limpar_checkpoints()
        st.success("Todos os dados foram apagados.")
        st.rerun()

    def _popular_dados_teste(self):
        popular_dados_teste(self.repo)
        st.success("Dados de teste criados.")
        st.rerun()

    def _remover_dados_teste(self):
        remover_dados_teste(self.repo)
        st.success("Dados de teste removidos.")
        st.rerun()

    def _resumo_periodos_divisao(self, divisao_id):
        tarefas = self.repo.listar_tarefas_da_divisao(divisao_id)
        return resumo_periodos_tarefas(tarefas)

    def _resumo_periodos_objetivo(self, objetivo_id, divisoes):
        tarefas_total = []
        for divisao in divisoes:
            if divisao["objetivo_id"] == objetivo_id:
                tarefas_total.extend(self.repo.listar_tarefas_da_divisao(divisao["id"]))
        return resumo_periodos_tarefas(tarefas_total)

    def _dados_estatistica_objetivos(self, objetivos, divisoes, periodo):
        dados = []
        for objetivo in objetivos:
            total, semana, hoje = self._resumo_periodos_objetivo(objetivo["id"], divisoes)
            valor = valor_por_periodo(total, semana, hoje, periodo)
            if valor > 0:
                dados.append(
                    {
                        "nome": objetivo["nome"],
                        "valor": valor,
                        "cor": objetivo.get("cor"),
                    }
                )
        return dados

    def _dados_estatistica_divisoes(self, divisoes, periodo):
        dados = []
        for divisao in divisoes:
            total, semana, hoje = self._resumo_periodos_divisao(divisao["id"])
            valor = valor_por_periodo(total, semana, hoje, periodo)
            if valor > 0:
                dados.append({"nome": divisao["nome"], "valor": valor})
        return dados

    @staticmethod
    def _data_humana_ptbr():
        semana = [
            "Segunda-Feira",
            "Terca-Feira",
            "Quarta-Feira",
            "Quinta-Feira",
            "Sexta-Feira",
            "Sabado",
            "Domingo",
        ]
        meses = [
            "Janeiro",
            "Fevereiro",
            "Marco",
            "Abril",
            "Maio",
            "Junho",
            "Julho",
            "Agosto",
            "Setembro",
            "Outubro",
            "Novembro",
            "Dezembro",
        ]

        agora = datetime.now()
        return f"{semana[agora.weekday()]}, {agora.day} de {meses[agora.month - 1]}"

    @staticmethod
    def _saudacao_thiago():
        hora = datetime.now().hour
        if hora < 12:
            return "Bom dia, Thiago"
        if hora < 18:
            return "Boa tarde, Thiago"
        return "Boa noite, Thiago"

    def executar(self):
        st.session_state._objetivos_tab_renderizado = False
        top_left, top_right = st.columns([3.2, 1.2], gap="small")
        with top_left:
            st.title("GEST\u00c3O DE TAREFAS")
            st.caption(self._saudacao_thiago())
            st.caption(self._data_humana_ptbr())

        with top_right:
            caminho_logo = Path(__file__).resolve().parent.parent / "logo.png"
            if caminho_logo.exists():
                st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
                st.image(str(caminho_logo), use_container_width=True)
        st.markdown(
            """
            <style>
            .dev-watermark {
                position: fixed;
                right: 14px;
                bottom: 10px;
                opacity: 0.30;
                font-size: 18px;
                letter-spacing: 0.4px;
                z-index: 9999;
                pointer-events: none;
                user-select: none;
            }
            </style>
            <div class="dev-watermark">DEV: Thiagoscocco 2026</div>
            """,
            unsafe_allow_html=True,
        )
        objetivos = self.repo.listar_objetivos()
        divisoes = self.repo.listar_divisoes()

        abas = st.tabs(
            [
                "Registro de Tarefa",
                "Objetivos",
                "Divisoes de Trabalho",
                "Estatisticas",
                "Configuracoes",
            ]
        )
        (
            aba_cronometro,
            aba_objetivos,
            aba_divisoes,
            aba_estatisticas,
            aba_config,
        ) = abas

        with aba_cronometro:
            render_cronometro_tab(
                objetivos=objetivos,
                divisoes=divisoes,
                cronometro=self.cronometro,
                tarefa_ativa_titulo=st.session_state.tarefa_ativa_titulo,
                tarefa_ativa_divisao_id=st.session_state.tarefa_ativa_divisao_id,
                label_divisao_fn=label_divisao,
                on_iniciar=self._iniciar_tarefa,
                on_pausar=self._pausar_tarefa,
                on_recomecar=self._recomecar_tarefa,
                on_parar_salvar=self._parar_e_salvar_tarefa,
                on_cancelar=self._cancelar_tarefa,
                on_remover_tempo=self._remover_tempo_tarefa,
                on_registrar_checkpoint=self._registrar_checkpoint_tarefa,
            )

        with aba_objetivos:
            render_objetivos_tab(
                objetivos=objetivos,
                divisoes=divisoes,
                resumo_objetivo_fn=lambda objetivo_id: self._resumo_periodos_objetivo(
                    objetivo_id, divisoes
                ),
                resumo_divisao_fn=self._resumo_periodos_divisao,
                on_criar_objetivo=self._criar_objetivo,
                on_apagar_objetivo=self._apagar_objetivo,
                on_randomizar_cores=self._randomizar_cores_objetivos,
            )

        with aba_divisoes:
            render_divisoes_tab(
                objetivos=objetivos,
                divisoes=divisoes,
                resumo_divisao_fn=self._resumo_periodos_divisao,
                listar_tarefas_da_divisao_fn=self.repo.listar_tarefas_da_divisao,
                on_criar_divisao=self._criar_divisao,
                on_apagar_divisao=self._apagar_divisao,
            )

        with aba_estatisticas:
            render_estatisticas_tab(
                dados_objetivos_por_periodo_fn=lambda periodo: self._dados_estatistica_objetivos(
                    objetivos, divisoes, periodo
                ),
                dados_divisoes_por_periodo_fn=lambda periodo: self._dados_estatistica_divisoes(
                    divisoes, periodo
                ),
            )

        with aba_config:
            render_configuracoes_tab(
                objetivos=objetivos,
                divisoes=divisoes,
                on_adicionar_tarefa_manual=self._adicionar_tarefa_manual,
                on_resetar=self._resetar_tudo,
            )

        if self.cronometro.rodando():
            time.sleep(0.2)
            st.rerun()
