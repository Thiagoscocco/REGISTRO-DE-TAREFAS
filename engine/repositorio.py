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
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _coluna_existe(self, conn, tabela, coluna):
        cur = conn.execute(f"PRAGMA table_info({tabela})")
        colunas = [row["name"] for row in cur.fetchall()]
        return coluna in colunas

    def _inicializar(self):
        with self._conectar() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS objetivos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL UNIQUE,
                    criado_em TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS divisoes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    objetivo_id INTEGER,
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

            if not self._coluna_existe(conn, "divisoes", "objetivo_id"):
                conn.execute("ALTER TABLE divisoes ADD COLUMN objetivo_id INTEGER")

            self._migrar_divisoes_sem_objetivo(conn)
            conn.commit()

    def _migrar_divisoes_sem_objetivo(self, conn):
        cur = conn.execute(
            "SELECT COUNT(*) AS total FROM divisoes WHERE objetivo_id IS NULL"
        )
        total_sem_objetivo = cur.fetchone()["total"]
        if total_sem_objetivo == 0:
            return

        agora = datetime.now().isoformat(timespec="seconds")
        conn.execute(
            """
            INSERT OR IGNORE INTO objetivos (nome, criado_em)
            VALUES ('Objetivo migrado', ?)
            """,
            (agora,),
        )
        objetivo_id = conn.execute(
            "SELECT id FROM objetivos WHERE nome = 'Objetivo migrado'"
        ).fetchone()["id"]
        conn.execute(
            "UPDATE divisoes SET objetivo_id = ? WHERE objetivo_id IS NULL",
            (objetivo_id,),
        )

    def criar_objetivo(self, nome):
        nome = (nome or "").strip()
        if not nome:
            raise ValueError("Nome do objetivo nao pode ser vazio.")
        agora = datetime.now().isoformat(timespec="seconds")
        with self._conectar() as conn:
            conn.execute(
                "INSERT INTO objetivos (nome, criado_em) VALUES (?, ?)",
                (nome, agora),
            )
            conn.commit()

    def listar_objetivos(self):
        with self._conectar() as conn:
            cur = conn.execute(
                """
                SELECT
                    o.id,
                    o.nome,
                    COALESCE(SUM(t.duracao_segundos), 0) AS total_segundos,
                    COUNT(DISTINCT d.id) AS total_divisoes,
                    COUNT(t.id) AS total_tarefas
                FROM objetivos o
                LEFT JOIN divisoes d ON d.objetivo_id = o.id
                LEFT JOIN tarefas t ON t.divisao_id = d.id
                GROUP BY o.id, o.nome
                ORDER BY o.nome COLLATE NOCASE ASC
                """
            )
            return [dict(row) for row in cur.fetchall()]

    def remover_objetivo(self, objetivo_id):
        with self._conectar() as conn:
            divisoes = conn.execute(
                "SELECT id FROM divisoes WHERE objetivo_id = ?",
                (int(objetivo_id),),
            ).fetchall()
            ids_divisoes = [row["id"] for row in divisoes]
            if ids_divisoes:
                placeholders = ",".join(["?"] * len(ids_divisoes))
                conn.execute(
                    f"DELETE FROM tarefas WHERE divisao_id IN ({placeholders})",
                    ids_divisoes,
                )
                conn.execute(
                    f"DELETE FROM divisoes WHERE id IN ({placeholders})",
                    ids_divisoes,
                )
            conn.execute("DELETE FROM objetivos WHERE id = ?", (int(objetivo_id),))
            conn.commit()

    def criar_divisao(self, objetivo_id, nome):
        nome = (nome or "").strip()
        if not nome:
            raise ValueError("Nome da divisao nao pode ser vazio.")
        if objetivo_id is None:
            raise ValueError("Selecione um objetivo.")

        agora = datetime.now().isoformat(timespec="seconds")
        with self._conectar() as conn:
            conn.execute(
                "INSERT INTO divisoes (objetivo_id, nome, criado_em) VALUES (?, ?, ?)",
                (int(objetivo_id), nome, agora),
            )
            conn.commit()

    def listar_divisoes(self):
        with self._conectar() as conn:
            cur = conn.execute(
                """
                SELECT
                    d.id,
                    d.nome,
                    d.objetivo_id,
                    o.nome AS objetivo_nome,
                    COALESCE(SUM(t.duracao_segundos), 0) AS total_segundos,
                    COUNT(t.id) AS total_tarefas
                FROM divisoes d
                LEFT JOIN objetivos o ON o.id = d.objetivo_id
                LEFT JOIN tarefas t ON t.divisao_id = d.id
                GROUP BY d.id, d.nome, d.objetivo_id, o.nome
                ORDER BY o.nome COLLATE NOCASE ASC, d.nome COLLATE NOCASE ASC
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
            conn.execute("DELETE FROM objetivos")
            conn.commit()

    @staticmethod
    def montar_intervalo_manual(data_tarefa, hora_tarefa, duracao_segundos):
        fim = datetime.combine(data_tarefa, hora_tarefa)
        inicio = fim - timedelta(seconds=float(duracao_segundos))
        return (
            inicio.isoformat(timespec="seconds"),
            fim.isoformat(timespec="seconds"),
        )
