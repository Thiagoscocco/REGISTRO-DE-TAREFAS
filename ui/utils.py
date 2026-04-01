from datetime import date, datetime, timedelta


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


def label_divisao(divisao):
    objetivo = divisao.get("objetivo_nome") or "Sem objetivo"
    return f"{objetivo} / {divisao['nome']}"


def resumo_periodos_tarefas(tarefas):
    hoje = date.today()
    inicio_semana = hoje - timedelta(days=hoje.weekday())

    total = 0.0
    semana = 0.0
    hoje_total = 0.0

    for tarefa in tarefas:
        duracao = float(tarefa.get("duracao_segundos") or 0.0)
        total += duracao

        data_ref = tarefa.get("fim_em") or tarefa.get("criado_em")
        try:
            dt_ref = datetime.fromisoformat(data_ref)
        except (TypeError, ValueError):
            continue

        data_ref_dia = dt_ref.date()
        if inicio_semana <= data_ref_dia <= hoje:
            semana += duracao
        if data_ref_dia == hoje:
            hoje_total += duracao

    return total, semana, hoje_total


def valor_por_periodo(total, semana, hoje_total, periodo):
    if periodo in {"Tempo semanal", "Tempo na semana"}:
        return semana
    if periodo == "Tempo hoje":
        return hoje_total
    return total


def formatar_tempo_padrao(segundos):
    if segundos is None:
        return "--"
    total = int(max(0, segundos))
    horas = total // 3600
    minutos = (total % 3600) // 60
    seg = total % 60
    return f"{horas}h {minutos}min {seg}seg"
