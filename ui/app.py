import time

import streamlit as st

from engine.cronometro import Cronometro, formatar_tempo


class App:
    def __init__(self):
        st.set_page_config(page_title="Cronometro de Atividades (pênis)", layout="centered")

        if "cronometro" not in st.session_state:
            st.session_state.cronometro = Cronometro()
        if "alvo_texto" not in st.session_state:
            st.session_state.alvo_texto = "0"

    @property
    def cronometro(self):
        return st.session_state.cronometro

    def _alvo_checkpoints(self):
        texto = st.session_state.alvo_texto.strip()
        if not texto:
            return 0
        try:
            valor = int(texto)
            return valor if valor >= 0 else 0
        except ValueError:
            return 0

    def _render_aba_cronometro(self, alvo_checkpoints):
        tempo = self.cronometro.tempo_total()
        st.markdown(f"## {formatar_tempo(tempo)}")

        est_restante = self.cronometro.estimativa_restante(alvo_checkpoints)
        if alvo_checkpoints > 0:
            texto_estimativa = (
                f"Previsao restante para {alvo_checkpoints} checkpoints: "
                f"{formatar_tempo(est_restante)}"
            )
        else:
            texto_estimativa = "Previsao restante: --"
        st.caption(texto_estimativa)

        col1, col2, col3 = st.columns(3)
        if col1.button("Iniciar tarefa", use_container_width=True):
            self.cronometro.iniciar()
            st.rerun()
        if col2.button("Pausar tarefa", use_container_width=True):
            self.cronometro.pausar()
            st.rerun()
        if col3.button("Concluir tarefa", use_container_width=True):
            self.cronometro.concluir()
            st.rerun()

        if st.button("Registrar checkpoint", use_container_width=True):
            self.cronometro.registrar_checkpoint()
            st.rerun()

        st.write(f"Checkpoints registrados: {self.cronometro.total_checkpoints()}")
        st.write(f"Tempo medio por checkpoint: {formatar_tempo(self.cronometro.media_intervalo())}")

    def _render_aba_previsoes(self, alvo_checkpoints):
        st.text_input(
            "Numero de checkpoints desejados:",
            key="alvo_texto",
        )

        est_total = self.cronometro.estimativa_total(alvo_checkpoints)
        est_restante = self.cronometro.estimativa_restante(alvo_checkpoints)
        media = self.cronometro.media_intervalo()

        st.write(f"Estimativa total: {formatar_tempo(est_total)}")
        st.write(f"Estimativa restante: {formatar_tempo(est_restante)}")

        if media is None:
            st.caption("Registre dois checkpoints para gerar previsao.")
        else:
            st.caption("Previsao atualizada com base no ritmo atual.")

    def executar(self):
        alvo_checkpoints = self._alvo_checkpoints()

        st.title("Cronometro de Atividades (Pênis)")
        aba_crono, aba_prev = st.tabs(["Cronometro", "Previsoes"])

        with aba_crono:
            self._render_aba_cronometro(alvo_checkpoints)
        with aba_prev:
            self._render_aba_previsoes(alvo_checkpoints)

        st.caption("dev Thiagoscocco 2024")

        if self.cronometro.rodando():
            time.sleep(0.2)
            st.rerun()
