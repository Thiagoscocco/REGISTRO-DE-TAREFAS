import time
from datetime import date, datetime, timedelta

import streamlit as st

from engine.cronometro import Cronometro, formatar_tempo
from engine.repositorio import RepositorioDados


def parse_duracao_hhmmss(texto):
    valor = (texto or "").strip()
    partes = valor.split(":")
    if len(partes) != 3:
        raise ValueError("Use o formato HH:MM:SS.")

    try:
        horas = int(partes[0])
        minutos = int(partes[1])
        segundos = int(partes[2])
    except ValueError as exc:
        raise ValueError("Duracao invalida. Use apenas numeros em HH:MM:SS.") from exc

    if horas < 0 or minutos < 0 or segundos < 0:
        raise ValueError("Duracao nao pode ser negativa.")
    if minutos > 59 or segundos > 59:
        raise ValueError("Minutos e segundos devem ficar entre 0 e 59.")

    total = horas * 3600 + minutos * 60 + segundos
    if total <= 0:
        raise ValueError("Duracao precisa ser maior que zero.")
    return float(total)


def formatar_data(texto_iso):
    if not texto_iso:
        return "--"
    try:
        dt = datetime.fromisoformat(texto_iso)
    except ValueError:
        return texto_iso
    return dt.strftime("%d/%m/%Y %H:%M")


class App:
    def __init__(self):
        st.set_page_config(page_title="Gestor de Tempo", layout="centered")

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

    def _label_divisao(self, divisao):
        objetivo = divisao["objetivo_nome"] or "Sem objetivo"
        return f"{objetivo} / {divisao['nome']}"

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

        st.session_state.tarefa_ativa_divisao_id = int(divisao_id)
        st.session_state.tarefa_ativa_titulo = titulo_limpo
        self.cronometro.iniciar()
        st.rerun()

    def _pausar_tarefa(self):
        self.cronometro.pausar()
        st.rerun()

    def _recomecar_tarefa(self):
        self.cronometro.recomecar()
        st.rerun()

    def _cancelar_tarefa(self):
        self.cronometro.resetar()
        self._limpar_tarefa_ativa()
        st.rerun()

    def _parar_e_salvar_tarefa(self, divisoes):
        divisao_id = st.session_state.tarefa_ativa_divisao_id
        titulo = st.session_state.tarefa_ativa_titulo
        if divisao_id is None or not titulo:
            st.warning("Nao existe tarefa ativa para salvar.")
            return

        duracao = self.cronometro.finalizar()
        if duracao <= 0:
            self._limpar_tarefa_ativa()
            st.warning("Tempo zerado. Nenhuma tarefa foi salva.")
            return

        divisao = self._divisao_por_id(divisoes, divisao_id)
        if divisao is None:
            self._limpar_tarefa_ativa()
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
        st.success("Tarefa salva com sucesso.")
        st.rerun()

    def _render_aba_cronometro(self, divisoes):
        st.subheader("Cronometro de tarefa")
        st.markdown(f"## {formatar_tempo(self.cronometro.tempo_total())}")

        if not divisoes:
            st.info("Crie ao menos uma divisao de trabalho na aba correspondente.")
            if self.cronometro.rodando() or self.cronometro.tempo_total() > 0:
                st.button(
                    "Cancelar tarefa atual",
                    on_click=self._cancelar_tarefa,
                    use_container_width=True,
                )
            return

        opcoes_divisao = [d["id"] for d in divisoes]
        mapa_divisoes = {d["id"]: self._label_divisao(d) for d in divisoes}
        divisao_ativa_id = st.session_state.tarefa_ativa_divisao_id
        tarefa_ativa = st.session_state.tarefa_ativa_titulo is not None

        default_id = divisao_ativa_id if divisao_ativa_id in mapa_divisoes else opcoes_divisao[0]
        indice_padrao = opcoes_divisao.index(default_id)

        divisao_selecionada = st.selectbox(
            "Divisao de trabalho",
            options=opcoes_divisao,
            index=indice_padrao,
            format_func=lambda item: mapa_divisoes[item],
            disabled=tarefa_ativa,
        )

        st.text_input(
            "Titulo da tarefa",
            key="input_titulo_tarefa",
            disabled=tarefa_ativa,
            placeholder="Ex: Aula 05 - classes em Python",
        )

        if tarefa_ativa:
            nome_divisao = mapa_divisoes.get(divisao_ativa_id, "Divisao removida")
            st.caption(
                f"Tarefa ativa: {st.session_state.tarefa_ativa_titulo} "
                f"(Divisao: {nome_divisao})"
            )

        if not tarefa_ativa:
            st.button(
                "Iniciar tarefa",
                on_click=self._iniciar_tarefa,
                args=(divisao_selecionada, st.session_state.input_titulo_tarefa),
                type="primary",
                use_container_width=True,
            )
            return

        col1, col2, col3 = st.columns(3)
        if self.cronometro.rodando():
            col1.button(
                "Pausar tarefa",
                on_click=self._pausar_tarefa,
                use_container_width=True,
            )
        else:
            col1.button(
                "Recomecar tarefa",
                on_click=self._recomecar_tarefa,
                use_container_width=True,
            )

        col2.button(
            "Parar e salvar",
            on_click=self._parar_e_salvar_tarefa,
            args=(divisoes,),
            type="primary",
            use_container_width=True,
        )
        col3.button(
            "Cancelar tarefa",
            on_click=self._cancelar_tarefa,
            use_container_width=True,
        )

    def _render_aba_objetivos(self, objetivos, divisoes):
        st.subheader("Objetivos")

        with st.form("form_criar_objetivo", clear_on_submit=True):
            nome_objetivo = st.text_input("Novo objetivo")
            enviado = st.form_submit_button("Criar objetivo")
            if enviado:
                try:
                    self.repo.criar_objetivo(nome_objetivo)
                    st.success("Objetivo criado.")
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))
                except Exception:
                    st.error("Nao foi possivel criar o objetivo. Nome pode ja existir.")

        if not objetivos:
            st.info("Nenhum objetivo criado ainda.")
            return

        for objetivo in objetivos:
            c1, c2, c3 = st.columns([6, 2, 2])
            c1.write(
                f"{objetivo['nome']} | Divisoes: {objetivo['total_divisoes']} | "
                f"Tarefas: {objetivo['total_tarefas']}"
            )
            c2.write(f"Total: {formatar_tempo(objetivo['total_segundos'])}")
            if c3.button("Apagar", key=f"apagar_objetivo_{objetivo['id']}"):
                divisoes_objetivo = [
                    d["id"] for d in divisoes if d["objetivo_id"] == objetivo["id"]
                ]
                if st.session_state.tarefa_ativa_divisao_id in divisoes_objetivo:
                    self.cronometro.resetar()
                    self._limpar_tarefa_ativa()
                self.repo.remover_objetivo(objetivo["id"])
                st.rerun()

    def _render_aba_divisoes(self, objetivos, divisoes):
        st.subheader("Divisoes de Trabalho")

        if not objetivos:
            st.info("Crie um objetivo primeiro para conseguir criar divisoes.")
        else:
            opcoes_objetivo = [o["id"] for o in objetivos]
            mapa_objetivo = {o["id"]: o["nome"] for o in objetivos}

            with st.form("form_criar_divisao", clear_on_submit=True):
                objetivo_id = st.selectbox(
                    "Objetivo",
                    options=opcoes_objetivo,
                    format_func=lambda item: mapa_objetivo[item],
                )
                nome_divisao = st.text_input("Nova divisao")
                enviado = st.form_submit_button("Criar divisao")
                if enviado:
                    try:
                        self.repo.criar_divisao(objetivo_id, nome_divisao)
                        st.success("Divisao criada.")
                        st.rerun()
                    except ValueError as exc:
                        st.error(str(exc))
                    except Exception:
                        st.error("Nao foi possivel criar a divisao. Nome pode ja existir.")

        if not divisoes:
            st.info("Nenhuma divisao criada ainda.")
            return

        total_geral = sum(d["total_segundos"] for d in divisoes)
        st.caption(
            f"Total acumulado geral: {formatar_tempo(total_geral)} "
            f"em {sum(d['total_tarefas'] for d in divisoes)} tarefas"
        )

        for divisao in divisoes:
            cabecalho = (
                f"{self._label_divisao(divisao)} | "
                f"Total: {formatar_tempo(divisao['total_segundos'])} | "
                f"Tarefas: {divisao['total_tarefas']}"
            )
            with st.expander(cabecalho, expanded=False):
                tarefas = self.repo.listar_tarefas_da_divisao(divisao["id"])
                if not tarefas:
                    st.caption("Sem tarefas registradas nesta divisao.")
                    continue

                for tarefa in tarefas:
                    c1, c2, c3, c4 = st.columns([5, 2, 3, 2])
                    c1.write(tarefa["titulo"])
                    c2.write(formatar_tempo(tarefa["duracao_segundos"]))
                    c3.write(formatar_data(tarefa["fim_em"] or tarefa["criado_em"]))
                    if c4.button("Remover", key=f"remover_tarefa_{tarefa['id']}"):
                        self.repo.remover_tarefa(tarefa["id"])
                        st.rerun()

    def _resumo_periodos_tarefas(self, tarefas):
        hoje = date.today()
        inicio_semana = hoje - timedelta(days=hoje.weekday())

        total = 0.0
        semana = 0.0
        hoje_total = 0.0

        for tarefa in tarefas:
            duracao = float(tarefa["duracao_segundos"] or 0.0)
            total += duracao

            data_ref = tarefa["fim_em"] or tarefa["criado_em"]
            try:
                dt_ref = datetime.fromisoformat(data_ref)
            except ValueError:
                continue

            data_ref_dia = dt_ref.date()
            if inicio_semana <= data_ref_dia <= hoje:
                semana += duracao
            if data_ref_dia == hoje:
                hoje_total += duracao

        return total, semana, hoje_total

    def _resumo_periodos_divisao(self, divisao_id):
        tarefas = self.repo.listar_tarefas_da_divisao(divisao_id)
        return self._resumo_periodos_tarefas(tarefas)

    def _resumo_periodos_objetivo(self, objetivo_id, divisoes):
        tarefas_total = []
        for divisao in divisoes:
            if divisao["objetivo_id"] == objetivo_id:
                tarefas_total.extend(self.repo.listar_tarefas_da_divisao(divisao["id"]))
        return self._resumo_periodos_tarefas(tarefas_total)

    def _render_aba_registros(self, objetivos, divisoes):
        st.subheader("Registros")

        st.markdown("### Objetivos")
        if not objetivos:
            st.info("Nenhum objetivo criado ainda.")
        else:
            for objetivo in objetivos:
                total, semana, hoje_total = self._resumo_periodos_objetivo(
                    objetivo["id"], divisoes
                )
                st.markdown(f"#### {objetivo['nome']}")
                col1, col2, col3 = st.columns(3)
                col1.metric("Horas Totais", formatar_tempo(total))
                col2.metric("Horas na semana", formatar_tempo(semana))
                col3.metric("Horas hoje", formatar_tempo(hoje_total))

        st.divider()
        st.markdown("### Divisoes de Trabalho")
        if not divisoes:
            st.info("Nenhuma divisao criada ainda.")
            return

        for divisao in divisoes:
            total, semana, hoje_total = self._resumo_periodos_divisao(divisao["id"])
            st.markdown(f"#### {self._label_divisao(divisao)}")
            col1, col2, col3 = st.columns(3)
            col1.metric("Horas Totais", formatar_tempo(total))
            col2.metric("Horas na semana", formatar_tempo(semana))
            col3.metric("Horas hoje", formatar_tempo(hoje_total))

    def _render_aba_configuracoes(self, divisoes):
        st.subheader("Configuracoes")
        st.markdown("### Adicionar tarefa manualmente")

        if not divisoes:
            st.info("Crie uma divisao de trabalho antes de adicionar tarefas.")
        else:
            opcoes_divisao = [d["id"] for d in divisoes]
            mapa_divisoes = {d["id"]: self._label_divisao(d) for d in divisoes}

            with st.form("form_tarefa_manual", clear_on_submit=True):
                divisao_manual = st.selectbox(
                    "Divisao",
                    options=opcoes_divisao,
                    format_func=lambda item: mapa_divisoes[item],
                )
                titulo_manual = st.text_input("Titulo da tarefa")
                duracao_manual = st.text_input(
                    "Duracao (HH:MM:SS)",
                    key="input_duracao_manual",
                )
                data_manual = st.date_input("Data da tarefa")
                hora_manual = st.time_input("Horario de termino")
                enviar_manual = st.form_submit_button("Adicionar tarefa manual")

                if enviar_manual:
                    try:
                        duracao_segundos = parse_duracao_hhmmss(duracao_manual)
                        inicio_em, fim_em = self.repo.montar_intervalo_manual(
                            data_manual,
                            hora_manual,
                            duracao_segundos,
                        )
                        self.repo.adicionar_tarefa(
                            divisao_id=divisao_manual,
                            titulo=titulo_manual,
                            duracao_segundos=duracao_segundos,
                            inicio_em=inicio_em,
                            fim_em=fim_em,
                            manual=True,
                        )
                        st.success("Tarefa manual adicionada.")
                        st.rerun()
                    except ValueError as exc:
                        st.error(str(exc))

        st.markdown("### Reset geral")
        st.caption(
            "Isso apaga todos os objetivos, todas as divisoes e todas as tarefas salvas."
        )
        confirmar_reset = st.checkbox("Confirmo que quero apagar tudo")
        if st.button("Apagar todos os dados", type="primary", use_container_width=True):
            if not confirmar_reset:
                st.warning("Marque a confirmacao para continuar.")
                return
            self.repo.resetar_tudo()
            self.cronometro.resetar()
            self._limpar_tarefa_ativa()
            st.success("Todos os dados foram apagados.")
            st.rerun()

    def executar(self):
        st.title("Gestao de Tempo")
        objetivos = self.repo.listar_objetivos()
        divisoes = self.repo.listar_divisoes()

        abas = st.tabs(
            [
                "Cronometro",
                "Objetivos",
                "Divisoes de Trabalho",
                "Registros",
                "Configuracoes",
            ]
        )
        aba_cronometro, aba_objetivos, aba_divisoes, aba_registros, aba_config = abas

        with aba_cronometro:
            self._render_aba_cronometro(divisoes)

        with aba_objetivos:
            self._render_aba_objetivos(objetivos, divisoes)

        with aba_divisoes:
            self._render_aba_divisoes(objetivos, divisoes)

        with aba_registros:
            self._render_aba_registros(objetivos, divisoes)

        with aba_config:
            self._render_aba_configuracoes(divisoes)

        if self.cronometro.rodando():
            time.sleep(0.2)
            st.rerun()
