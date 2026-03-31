import sqlite3
from datetime import datetime, timedelta
from pathlib import Path


class RepositorioDados:
    def __init__(self, caminho_db="data/app.db"):
        self._caminho_db = Path(caminho_db)
        self._caminho_db.parent.mkdir(parents=True, exist_ok=True)
        self._inicializar()

    def _conectar(self):
        conn = sqlite3.connect(self._caminho_db)
        conn.row_factory = sqlite3.Row
        return conn

    def _inicializar(self):
        with self._conectar() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS divisoes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL UNIQUE,
                    criado_em TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tarefas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    divisao_id INTEGER NOT NULL,
                    titulo TEXT NOT NULL,
                    duracao_segundos REAL NOT NULL,
                    inicio_em TEXT,
                    fim_em TEXT,
                    manual INTEGER NOT NULL DEFAULT 0,
                    criado_em TEXT NOT NULL,
                    FOREIGN KEY(divisao_id) REFERENCES divisoes(id) ON DELETE CASCADE
                )
                """
            )
            conn.commit()

    def criar_divisao(self, nome):
        nome = (nome or "").strip()
        if not nome:
            raise ValueError("Nome da divisao nao pode ser vazio.")

        agora = datetime.now().isoformat(timespec="seconds")
        with self._conectar() as conn:
            conn.execute(
                "INSERT INTO divisoes (nome, criado_em) VALUES (?, ?)",
                (nome, agora),
            )
            conn.commit()

    def listar_divisoes(self):
        with self._conectar() as conn:
            cur = conn.execute(
                """
                SELECT
                    d.id,
                    d.nome,
                    COALESCE(SUM(t.duracao_segundos), 0) AS total_segundos,
                    COUNT(t.id) AS total_tarefas
                FROM divisoes d
                LEFT JOIN tarefas t ON t.divisao_id = d.id
                GROUP BY d.id, d.nome
                ORDER BY d.nome COLLATE NOCASE ASC
                """
            )
            return [dict(row) for row in cur.fetchall()]

    def adicionar_tarefa(
        self,
        divisao_id,
        titulo,
        duracao_segundos,
        inicio_em=None,
        fim_em=None,
        manual=False,
    ):
        titulo = (titulo or "").strip()
        if not titulo:
            raise ValueError("Titulo da tarefa nao pode ser vazio.")
        if duracao_segundos <= 0:
            raise ValueError("Duracao precisa ser maior que zero.")

        agora = datetime.now().isoformat(timespec="seconds")
        with self._conectar() as conn:
            conn.execute(
                """
                INSERT INTO tarefas (
                    divisao_id, titulo, duracao_segundos, inicio_em, fim_em, manual, criado_em
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    int(divisao_id),
                    titulo,
                    float(duracao_segundos),
                    inicio_em,
                    fim_em,
                    1 if manual else 0,
                    agora,
                ),
            )
            conn.commit()

    def listar_tarefas_da_divisao(self, divisao_id):
        with self._conectar() as conn:
            cur = conn.execute(
                """
                SELECT
                    id,
                    titulo,
                    duracao_segundos,
                    inicio_em,
                    fim_em,
                    manual,
                    criado_em
                FROM tarefas
                WHERE divisao_id = ?
                ORDER BY id DESC
                """,
                (int(divisao_id),),
            )
            return [dict(row) for row in cur.fetchall()]

    def remover_tarefa(self, tarefa_id):
        with self._conectar() as conn:
            conn.execute("DELETE FROM tarefas WHERE id = ?", (int(tarefa_id),))
            conn.commit()

    def resetar_tudo(self):
        with self._conectar() as conn:
            conn.execute("DELETE FROM tarefas")
            conn.execute("DELETE FROM divisoes")
            conn.commit()

    @staticmethod
    def montar_intervalo_manual(data_tarefa, hora_tarefa, duracao_segundos):
        fim = datetime.combine(data_tarefa, hora_tarefa)
        inicio = fim - timedelta(seconds=float(duracao_segundos))
        return (
            inicio.isoformat(timespec="seconds"),
            fim.isoformat(timespec="seconds"),
        )
