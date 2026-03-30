import tkinter as tk
from tkinter import ttk
from tkinter import font as tkfont

from engine.cronometro import Cronometro, formatar_tempo


class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Cronometro de Atividades")
        self.root.resizable(False, False)

        self._definir_estilo()
        self._centralizar_janela(520, 320)

        self.cronometro = Cronometro()
        self.alvo_checkpoints = 0

        self._criar_componentes()
        self._registrar_atalhos()
        self._atualizar_tempo()

    def _definir_estilo(self):
        estilo = ttk.Style()
        try:
            estilo.theme_use("clam")
        except tk.TclError:
            pass
        estilo.configure("TNotebook", padding=4)
        estilo.configure("TNotebook.Tab", padding=(10, 6))

    def _centralizar_janela(self, largura, altura):
        self.root.update_idletasks()
        tela_largura = self.root.winfo_screenwidth()
        tela_altura = self.root.winfo_screenheight()
        x = int((tela_largura - largura) / 2)
        y = int((tela_altura - altura) / 2)
        self.root.geometry(f"{largura}x{altura}+{x}+{y}")

    def _criar_componentes(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=8, pady=8)

        self.aba_crono = ttk.Frame(self.notebook)
        self.aba_prev = ttk.Frame(self.notebook)

        self.notebook.add(self.aba_crono, text="Cronometro")
        self.notebook.add(self.aba_prev, text="Previsoes")

        self._criar_aba_crono()
        self._criar_aba_prev()

        marca = ttk.Label(self.root, text="dev Thiagoscocco 2026", foreground="#888888")
        marca.place(relx=1.0, rely=1.0, anchor="se", x=-6, y=-4)

    def _criar_aba_crono(self):
        self.timer_font = tkfont.Font(family="Helvetica", size=28, weight="bold")
        self.sub_font = tkfont.Font(family="Helvetica", size=10)
        self.info_font = tkfont.Font(family="Helvetica", size=11)

        self.lbl_tempo = ttk.Label(self.aba_crono, text="00:00:00", font=self.timer_font)
        self.lbl_tempo.pack(pady=(14, 6))

        self.lbl_estimativa = ttk.Label(
            self.aba_crono,
            text="Previsao restante: --",
            font=self.sub_font,
            foreground="#555555",
        )
        self.lbl_estimativa.pack(pady=(0, 10))

        botoes = ttk.Frame(self.aba_crono)
        botoes.pack(pady=4)

        self.btn_iniciar = ttk.Button(botoes, text="Iniciar tarefa", command=self._acao_iniciar)
        self.btn_iniciar.grid(row=0, column=0, padx=6, pady=4)

        self.btn_pausar = ttk.Button(botoes, text="Pausar tarefa", command=self._acao_pausar)
        self.btn_pausar.grid(row=0, column=1, padx=6, pady=4)

        self.btn_concluir = ttk.Button(botoes, text="Concluir tarefa", command=self._acao_concluir)
        self.btn_concluir.grid(row=0, column=2, padx=6, pady=4)

        self.btn_checkpoint = ttk.Button(botoes, text="Registrar checkpoint", command=self._acao_checkpoint)
        self.btn_checkpoint.grid(row=1, column=0, columnspan=3, padx=6, pady=6, sticky="ew")

        info = ttk.Frame(self.aba_crono)
        info.pack(pady=(6, 0))

        self.lbl_checkpoints = ttk.Label(info, text="Checkpoints registrados: 0", font=self.info_font)
        self.lbl_checkpoints.pack()

        self.lbl_media = ttk.Label(info, text="Tempo medio por checkpoint: --", font=self.info_font)
        self.lbl_media.pack()

    def _criar_aba_prev(self):
        container = ttk.Frame(self.aba_prev)
        container.pack(fill="both", expand=True, padx=10, pady=10)

        entrada_frame = ttk.Frame(container)
        entrada_frame.pack(fill="x", pady=(6, 10))

        ttk.Label(entrada_frame, text="Numero de checkpoints desejados:").pack(side="left")

        self.var_alvo = tk.StringVar(value="0")
        self.var_alvo.trace_add("write", self._on_alvo_change)

        self.entry_alvo = ttk.Entry(entrada_frame, textvariable=self.var_alvo, width=8)
        self.entry_alvo.pack(side="left", padx=8)

        self.lbl_total_prev = ttk.Label(container, text="Estimativa total: --")
        self.lbl_total_prev.pack(anchor="w", pady=4)

        self.lbl_restante_prev = ttk.Label(container, text="Estimativa restante: --")
        self.lbl_restante_prev.pack(anchor="w", pady=4)

        self.lbl_status_prev = ttk.Label(container, text="Registre dois checkpoints para gerar previsao.", foreground="#666666")
        self.lbl_status_prev.pack(anchor="w", pady=(10, 0))

    def _registrar_atalhos(self):
        self.root.bind("<Return>", self._atalho_iniciar)
        self.root.bind("<space>", self._atalho_checkpoint)

    def _acao_iniciar(self):
        self.cronometro.iniciar()
        self._atualizar_info()

    def _acao_pausar(self):
        self.cronometro.pausar()
        self._atualizar_info()

    def _acao_concluir(self):
        self.cronometro.concluir()
        self._atualizar_info()

    def _acao_checkpoint(self):
        self.cronometro.registrar_checkpoint()
        self._atualizar_info()

    def _atalho_iniciar(self, event):
        foco = self.root.focus_get()
        if foco is not None and foco.winfo_class() in ("TEntry", "Entry"):
            return
        self._acao_iniciar()

    def _atalho_checkpoint(self, event):
        foco = self.root.focus_get()
        if foco is not None and foco.winfo_class() in ("TEntry", "Entry"):
            return
        self._acao_checkpoint()

    def _on_alvo_change(self, *args):
        texto = self.var_alvo.get().strip()
        if not texto:
            self.alvo_checkpoints = 0
            self._atualizar_info()
            return
        try:
            valor = int(texto)
            if valor < 0:
                valor = 0
            self.alvo_checkpoints = valor
        except ValueError:
            self.alvo_checkpoints = 0
        self._atualizar_info()

    def _atualizar_tempo(self):
        tempo = self.cronometro.tempo_total()
        self.lbl_tempo.config(text=formatar_tempo(tempo))
        self.root.after(200, self._atualizar_tempo)

    def _atualizar_info(self):
        total_cp = self.cronometro.total_checkpoints()
        self.lbl_checkpoints.config(text=f"Checkpoints registrados: {total_cp}")

        media = self.cronometro.media_intervalo()
        self.lbl_media.config(text=f"Tempo medio por checkpoint: {formatar_tempo(media)}")

        est_total = self.cronometro.estimativa_total(self.alvo_checkpoints)
        est_restante = self.cronometro.estimativa_restante(self.alvo_checkpoints)

        self.lbl_total_prev.config(text=f"Estimativa total: {formatar_tempo(est_total)}")
        self.lbl_restante_prev.config(text=f"Estimativa restante: {formatar_tempo(est_restante)}")

        if media is None:
            self.lbl_status_prev.config(text="Registre dois checkpoints para gerar previsao.")
        else:
            self.lbl_status_prev.config(text="Previsao atualizada com base no ritmo atual.")

        if self.alvo_checkpoints > 0:
            texto = f"Previsao restante para {self.alvo_checkpoints} checkpoints: {formatar_tempo(est_restante)}"
        else:
            texto = "Previsao restante: --"
        self.lbl_estimativa.config(text=texto)

    def executar(self):
        self.root.mainloop()
