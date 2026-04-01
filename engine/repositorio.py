import random
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path


class RepositorioDados:
    _PALETA_OBJETIVOS = [
        "#5B8D8D",
        "#CDB981",
        "#B45E5E",
        "#7A8D9E",
        "#4A4A4A",
        "#6E665B",
        "#6A9998",
        "#77A5A3",
        "#86B2AE",
        "#A99765",
        "#B6A572",
        "#C1B07C",
        "#9F5555",
        "#AA5A5A",
        "#C36A6A",
        "#6D8194",
        "#637789",
        "#8799A9",
        "#555555",
        "#626262",
        "#6F6F6F",
        "#7A7266",
        "#867D70",
        "#91887A",
    ]

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
                    criado_em TEXT NOT NULL,
                    cor TEXT,
                    origem TEXT NOT NULL DEFAULT 'user'
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS divisoes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    objetivo_id INTEGER,
                    nome TEXT NOT NULL UNIQUE,
                    criado_em TEXT NOT NULL,
                    origem TEXT NOT NULL DEFAULT 'user',
                    FOREIGN KEY(objetivo_id) REFERENCES objetivos(id) ON DELETE CASCADE
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
                    origem TEXT NOT NULL DEFAULT 'user',
                    FOREIGN KEY(divisao_id) REFERENCES divisoes(id) ON DELETE CASCADE
                )
                """
            )

            if not self._coluna_existe(conn, "divisoes", "objetivo_id"):
                conn.execute("ALTER TABLE divisoes ADD COLUMN objetivo_id INTEGER")
            if not self._coluna_existe(conn, "objetivos", "origem"):
                conn.execute(
                    "ALTER TABLE objetivos ADD COLUMN origem TEXT NOT NULL DEFAULT 'user'"
                )
            if not self._coluna_existe(conn, "objetivos", "cor"):
                conn.execute("ALTER TABLE objetivos ADD COLUMN cor TEXT")
            if not self._coluna_existe(conn, "divisoes", "origem"):
                conn.execute(
                    "ALTER TABLE divisoes ADD COLUMN origem TEXT NOT NULL DEFAULT 'user'"
                )
            if not self._coluna_existe(conn, "tarefas", "origem"):
                conn.execute(
                    "ALTER TABLE tarefas ADD COLUMN origem TEXT NOT NULL DEFAULT 'user'"
                )

            self._migrar_divisoes_sem_objetivo(conn)
            self._migrar_cores_objetivos(conn)
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

    def _proxima_cor_disponivel(self, cores_em_uso):
        for cor in self._PALETA_OBJETIVOS:
            if cor not in cores_em_uso:
                return cor

        indice = 0
        while True:
            r = (73 * (indice + 3)) % 256
            g = (131 * (indice + 5)) % 256
            b = (191 * (indice + 7)) % 256
            cor = f"#{r:02X}{g:02X}{b:02X}"
            if cor not in cores_em_uso:
                return cor
            indice += 1

    def _migrar_cores_objetivos(self, conn):
        cores_em_uso = set()
        cur_objetivos = conn.execute("SELECT id, cor FROM objetivos ORDER BY id ASC")
        for row in cur_objetivos.fetchall():
            cor = row["cor"]
            if (not cor) or (cor in cores_em_uso) or (cor not in self._PALETA_OBJETIVOS):
                cor = self._proxima_cor_disponivel(cores_em_uso)
                conn.execute("UPDATE objetivos SET cor = ? WHERE id = ?", (cor, row["id"]))
            cores_em_uso.add(cor)

    def criar_objetivo(self, nome, origem="user"):
        nome = (nome or "").strip()
        if not nome:
            raise ValueError("Nome do objetivo nao pode ser vazio.")
        agora = datetime.now().isoformat(timespec="seconds")
        with self._conectar() as conn:
            cur_cores = conn.execute(
                "SELECT cor FROM objetivos WHERE cor IS NOT NULL AND cor != ''"
            )
            cores_em_uso = {row["cor"] for row in cur_cores.fetchall()}
            cor = self._proxima_cor_disponivel(cores_em_uso)

            cur = conn.execute(
                "INSERT INTO objetivos (nome, criado_em, cor, origem) VALUES (?, ?, ?, ?)",
                (nome, agora, cor, origem),
            )
            conn.commit()
            return int(cur.lastrowid)

    def obter_objetivo_por_nome(self, nome):
        with self._conectar() as conn:
            cur = conn.execute(
                "SELECT id, nome, criado_em, origem FROM objetivos WHERE nome = ?",
                ((nome or "").strip(),),
            )
            row = cur.fetchone()
            return dict(row) if row else None

    def listar_objetivos(self):
        with self._conectar() as conn:
            cur = conn.execute(
                """
                SELECT
                    o.id,
                    o.nome,
                    o.cor,
                    COALESCE(SUM(t.duracao_segundos), 0) AS total_segundos,
                    COUNT(DISTINCT d.id) AS total_divisoes,
                    COUNT(t.id) AS total_tarefas
                FROM objetivos o
                LEFT JOIN divisoes d ON d.objetivo_id = o.id
                LEFT JOIN tarefas t ON t.divisao_id = d.id
                GROUP BY o.id, o.nome, o.cor
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

    def criar_divisao(self, objetivo_id, nome, origem="user"):
        nome = (nome or "").strip()
        if not nome:
            raise ValueError("Nome da divisao nao pode ser vazio.")
        if objetivo_id is None:
            raise ValueError("Selecione um objetivo.")

        agora = datetime.now().isoformat(timespec="seconds")
        with self._conectar() as conn:
            cur = conn.execute(
                """
                INSERT INTO divisoes (objetivo_id, nome, criado_em, origem)
                VALUES (?, ?, ?, ?)
                """,
                (int(objetivo_id), nome, agora, origem),
            )
            conn.commit()
            return int(cur.lastrowid)

    def obter_divisao_por_nome(self, nome):
        with self._conectar() as conn:
            cur = conn.execute(
                """
                SELECT id, objetivo_id, nome, criado_em, origem
                FROM divisoes
                WHERE nome = ?
                """,
                ((nome or "").strip(),),
            )
            row = cur.fetchone()
            return dict(row) if row else None

    def listar_divisoes(self):
        with self._conectar() as conn:
            cur = conn.execute(
                """
                SELECT
                    d.id,
                    d.nome,
                    d.objetivo_id,
                    o.nome AS objetivo_nome,
                    o.cor AS objetivo_cor,
                    COALESCE(SUM(t.duracao_segundos), 0) AS total_segundos,
                    COUNT(t.id) AS total_tarefas,
                    COALESCE(MAX(COALESCE(t.fim_em, t.criado_em)), d.criado_em) AS ultima_atualizacao
                FROM divisoes d
                LEFT JOIN objetivos o ON o.id = d.objetivo_id
                LEFT JOIN tarefas t ON t.divisao_id = d.id
                GROUP BY d.id, d.nome, d.objetivo_id, o.nome, o.cor
                ORDER BY ultima_atualizacao DESC, d.nome COLLATE NOCASE ASC
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
        origem="user",
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
                    divisao_id, titulo, duracao_segundos, inicio_em, fim_em, manual, criado_em, origem
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    int(divisao_id),
                    titulo,
                    float(duracao_segundos),
                    inicio_em,
                    fim_em,
                    1 if manual else 0,
                    agora,
                    origem,
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

    def remover_divisao(self, divisao_id):
        with self._conectar() as conn:
            conn.execute("DELETE FROM tarefas WHERE divisao_id = ?", (int(divisao_id),))
            conn.execute("DELETE FROM divisoes WHERE id = ?", (int(divisao_id),))
            conn.commit()

    def resetar_tudo(self):
        with self._conectar() as conn:
            conn.execute("DELETE FROM tarefas")
            conn.execute("DELETE FROM divisoes")
            conn.execute("DELETE FROM objetivos")
            conn.commit()

    def limpar_por_origem(self, origem):
        with self._conectar() as conn:
            conn.execute("DELETE FROM tarefas WHERE origem = ?", (origem,))
            conn.execute("DELETE FROM divisoes WHERE origem = ?", (origem,))
            conn.execute("DELETE FROM objetivos WHERE origem = ?", (origem,))
            conn.commit()

    def randomizar_cores_objetivos(self):
        with self._conectar() as conn:
            cur = conn.execute("SELECT id FROM objetivos ORDER BY id ASC")
            objetivos = cur.fetchall()
            if not objetivos:
                return 0

            rng = random.Random()
            cores_usadas = set()
            for row in objetivos:
                while True:
                    r = rng.randint(58, 182)
                    g = rng.randint(58, 182)
                    b = rng.randint(58, 182)
                    cor = f"#{r:02X}{g:02X}{b:02X}"
                    if cor not in cores_usadas:
                        break
                conn.execute("UPDATE objetivos SET cor = ? WHERE id = ?", (cor, row["id"]))
                cores_usadas.add(cor)

            conn.commit()
            return len(objetivos)

    @staticmethod
    def montar_intervalo_manual(data_tarefa, hora_tarefa, duracao_segundos):
        fim = datetime.combine(data_tarefa, hora_tarefa)
        inicio = fim - timedelta(seconds=float(duracao_segundos))
        return (
            inicio.isoformat(timespec="seconds"),
            fim.isoformat(timespec="seconds"),
        )
