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
        self._inicio = 0.0
        self._acumulado = 0.0

    def iniciar(self):
        self.resetar()
        self._rodando = True
        self._inicio = time.perf_counter()

    def rodando(self):
        return self._rodando

    def pausar(self):
        if not self._rodando:
            return
        agora = time.perf_counter()
        self._acumulado += agora - self._inicio
        self._rodando = False
        self._inicio = 0.0

    def recomecar(self):
        if not self._rodando:
            self._rodando = True
            self._inicio = time.perf_counter()

    def resetar(self):
        self._rodando = False
        self._inicio = 0.0
        self._acumulado = 0.0

    def tempo_total(self):
        if self._rodando:
            return self._acumulado + (time.perf_counter() - self._inicio)
        return self._acumulado

    def finalizar(self):
        total = self.tempo_total()
        self.resetar()
        return total
