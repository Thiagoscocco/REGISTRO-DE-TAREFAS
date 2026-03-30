import time


def formatar_tempo(segundos):
    if segundos is None:
        return "--"
    if segundos < 0:
        segundos = 0
    total = int(segundos)
    horas = total // 3600
    minutos = (total % 3600) // 60
    seg = total % 60
    return f"{horas:02d}:{minutos:02d}:{seg:02d}"


class Cronometro:
    def __init__(self):
        self._rodando = False
        self._inicio = None
        self._acumulado = 0.0
        self._ultimo_checkpoint = None
        self._intervalos = []
        self._total_checkpoints = 0

    def iniciar(self):
        if self._rodando:
            return
        self._rodando = True
        self._inicio = time.perf_counter()
        if self._ultimo_checkpoint is not None:
            # evita contar o tempo pausado no proximo intervalo
            self._ultimo_checkpoint = self._inicio

    def rodando(self):
        return self._rodando

    def concluir(self):
        self.resetar()

    def pausar(self):
        if not self._rodando:
            return
        agora = time.perf_counter()
        self._acumulado += agora - self._inicio
        self._inicio = None
        self._rodando = False

    def resetar(self):
        self._rodando = False
        self._inicio = None
        self._acumulado = 0.0
        self._ultimo_checkpoint = None
        self._intervalos = []
        self._total_checkpoints = 0

    def tempo_total(self):
        if self._rodando:
            return self._acumulado + (time.perf_counter() - self._inicio)
        return self._acumulado

    def registrar_checkpoint(self):
        if not self._rodando:
            return None
        agora = time.perf_counter()
        self._total_checkpoints += 1
        if self._ultimo_checkpoint is None:
            self._ultimo_checkpoint = agora
            return None
        intervalo = agora - self._ultimo_checkpoint
        self._intervalos.append(intervalo)
        self._ultimo_checkpoint = agora
        return intervalo

    def media_intervalo(self):
        if not self._intervalos:
            return None
        return sum(self._intervalos) / len(self._intervalos)

    def total_checkpoints(self):
        return self._total_checkpoints

    def estimativa_restante(self, alvo_checkpoints):
        media = self.media_intervalo()
        if media is None:
            return None
        restante = alvo_checkpoints - self._total_checkpoints
        if restante < 0:
            restante = 0
        return media * restante

    def estimativa_total(self, alvo_checkpoints):
        media = self.media_intervalo()
        if media is None:
            return None
        if alvo_checkpoints < 0:
            alvo_checkpoints = 0
        return media * alvo_checkpoints
