import random
from datetime import datetime, timedelta


ORIGEM_TESTE = "demo"


def _gerar_fim_aleatorio(rng, agora):
    dias_atras = rng.randint(0, 20)
    horas = rng.randint(0, 9)
    minutos = rng.randint(0, 59)
    return agora - timedelta(days=dias_atras, hours=horas, minutes=minutos)


def _nome_divisao_teste(nome_base, repositorio, objetivo_id):
    divisao = repositorio.obter_divisao_por_nome(nome_base)
    if not divisao:
        return nome_base
    if divisao["objetivo_id"] == objetivo_id:
        return nome_base

    candidato = f"{nome_base} (Teste)"
    contador = 2
    while repositorio.obter_divisao_por_nome(candidato):
        candidato = f"{nome_base} (Teste {contador})"
        contador += 1
    return candidato


def popular_dados_teste(repositorio):
    repositorio.limpar_por_origem(ORIGEM_TESTE)
    rng = random.Random(42)
    agora = datetime.now().replace(microsecond=0)

    estrutura = {
        "Python": {
            "Curso de Python": [
                "Aula de funcoes",
                "Pratica de classes",
                "Revisao de modulos",
            ],
            "Projeto API": [
                "Modelagem de endpoints",
                "Ajuste de autenticacao",
            ],
        },
        "Trabalho": {
            "Reunioes": [
                "Alinhamento semanal",
                "Call com cliente",
            ],
            "Execucao": [
                "Implementacao de demanda",
                "Documentacao tecnica",
            ],
        },
        "Faculdade": {
            "Estudos": [
                "Resumo da materia",
                "Lista de exercicios",
            ],
            "Projetos": [
                "Avanco do trabalho final",
                "Pesquisa bibliografica",
            ],
        },
        "Lazer": {
            "Leitura": [
                "Leitura de livro",
                "Anotacoes pessoais",
            ],
            "Filmes e Series": [
                "Episodio da semana",
            ],
        },
    }

    for nome_objetivo, divisoes in estrutura.items():
        objetivo = repositorio.obter_objetivo_por_nome(nome_objetivo)
        if objetivo:
            objetivo_id = objetivo["id"]
        else:
            objetivo_id = repositorio.criar_objetivo(nome_objetivo, origem=ORIGEM_TESTE)

        for nome_divisao, tarefas in divisoes.items():
            nome_final_divisao = _nome_divisao_teste(
                nome_divisao, repositorio, objetivo_id
            )
            divisao = repositorio.obter_divisao_por_nome(nome_final_divisao)
            if divisao:
                divisao_id = divisao["id"]
            else:
                divisao_id = repositorio.criar_divisao(
                    objetivo_id,
                    nome_final_divisao,
                    origem=ORIGEM_TESTE,
                )

            for titulo in tarefas:
                duracao_segundos = rng.randint(25, 180) * 60
                fim = _gerar_fim_aleatorio(rng, agora)
                inicio = fim - timedelta(seconds=duracao_segundos)
                repositorio.adicionar_tarefa(
                    divisao_id=divisao_id,
                    titulo=titulo,
                    duracao_segundos=duracao_segundos,
                    inicio_em=inicio.isoformat(timespec="seconds"),
                    fim_em=fim.isoformat(timespec="seconds"),
                    manual=True,
                    origem=ORIGEM_TESTE,
                )


def remover_dados_teste(repositorio):
    repositorio.limpar_por_origem(ORIGEM_TESTE)
