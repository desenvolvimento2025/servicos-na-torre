"""
Camada de dados do Serviços na Torre.

O "repositório" (item 2 do documento de requisitos) é um banco SQLite local
(arquivo data/servicos_na_torre.db). As planilhas Excel continuam sendo a
fonte de entrada (Serviços, Usuários, Status) e são importadas para dentro
deste banco pelas funções import_*.

Campos controlados PELO WEBAPP (nunca sobrescritos pela reimportação da
planilha): status_monitor, programador, tempo_resposta1,
programador_vinculado, data_hora_vinculo, status_atendimento (após criado).
"""
import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime

import pandas as pd

from . import config

_SCHEMA = """
CREATE TABLE IF NOT EXISTS servicos (
    id_atendimento TEXT PRIMARY KEY,
    data_inicio TEXT,
    tipo_servico TEXT,
    urgente TEXT,
    solicitante TEXT,
    local_origem TEXT,
    local_destino TEXT,
    percurso TEXT,
    observacoes TEXT,
    placa TEXT,
    motorista TEXT,
    telefone_contato TEXT,
    campos_extra TEXT,              -- JSON com colunas da planilha não mapeadas
    status_atendimento TEXT,        -- controlado pelo webapp (PENDENTE / ABERTO / ...)
    status_monitor TEXT,
    programador TEXT,
    tempo_resposta1 TEXT,
    programador_vinculado TEXT DEFAULT 'NAO',
    data_hora_vinculo TEXT,
    criado_em TEXT,
    atualizado_em TEXT
);

CREATE TABLE IF NOT EXISTS usuarios (
    nome TEXT PRIMARY KEY,
    email TEXT,
    cpf TEXT,
    telefone TEXT,
    filial TEXT,
    grupo TEXT,
    eh_programador TEXT
);

CREATE TABLE IF NOT EXISTS status_opcoes (
    status TEXT PRIMARY KEY,
    descricao TEXT
);

CREATE TABLE IF NOT EXISTS comentarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    servico_id TEXT,
    data_hora TEXT,
    autor TEXT,
    tipo TEXT,          -- 'automatico' ou 'manual'
    texto TEXT,
    FOREIGN KEY (servico_id) REFERENCES servicos (id_atendimento)
);
"""


@contextmanager
def get_connection():
    os.makedirs(os.path.dirname(config.DB_PATH), exist_ok=True)
    conn = sqlite3.connect(config.DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_connection() as conn:
        conn.executescript(_SCHEMA)


def _now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def add_comentario(conn, servico_id, autor, texto, tipo="automatico"):
    conn.execute(
        "INSERT INTO comentarios (servico_id, data_hora, autor, tipo, texto) "
        "VALUES (?, ?, ?, ?, ?)",
        (servico_id, _now_str(), autor, tipo, texto),
    )


# ---------------------------------------------------------------------------
# Importação das planilhas Excel
# ---------------------------------------------------------------------------
def import_servicos_excel(caminho=None):
    """Item 6: lê a planilha 'solicitações-crane' e cria/atualiza a tabela
    'servicos'. Novos registros entram com STATUS_MONITOR = PENDENTE e
    ganham um log de chegada. Registros existentes só têm os campos vindos
    da planilha atualizados (incluindo o 'Status do atendimento' original
    do Koepe, que é só informativo); os campos controlados pelo webapp
    (status_monitor, programador, tempo_resposta1, programador_vinculado,
    data_hora_vinculo) nunca são tocados pela importação."""
    caminho = caminho or config.ARQ_SERVICOS
    df = pd.read_excel(caminho)

    novos, atualizados = 0, 0
    with get_connection() as conn:
        for _, row in df.iterrows():
            campos = {}
            extras = {}
            for col_excel, valor in row.items():
                if pd.isna(valor):
                    valor = None
                elif isinstance(valor, (pd.Timestamp, datetime)):
                    valor = str(valor)
                campo_interno = config.COLUNAS_SERVICOS.get(col_excel)
                if campo_interno:
                    campos[campo_interno] = valor
                else:
                    extras[col_excel] = valor

            id_atendimento = str(campos.get("id_atendimento"))
            if not id_atendimento or id_atendimento == "None":
                continue  # linha sem id, ignora

            existente = conn.execute(
                "SELECT id_atendimento FROM servicos WHERE id_atendimento = ?",
                (id_atendimento,),
            ).fetchone()

            if existente is None:
                conn.execute(
                    """INSERT INTO servicos (
                        id_atendimento, data_inicio, tipo_servico, urgente, solicitante,
                        local_origem, local_destino, percurso, observacoes, placa,
                        motorista, telefone_contato, campos_extra,
                        status_atendimento, status_monitor, programador,
                        tempo_resposta1, programador_vinculado, data_hora_vinculo,
                        criado_em, atualizado_em
                    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        id_atendimento,
                        campos.get("data_inicio"),
                        campos.get("tipo_servico"),
                        campos.get("urgente"),
                        campos.get("solicitante"),
                        campos.get("local_origem"),
                        campos.get("local_destino"),
                        campos.get("percurso"),
                        campos.get("observacoes"),
                        campos.get("placa"),
                        campos.get("motorista"),
                        campos.get("telefone_contato"),
                        json.dumps(extras, ensure_ascii=False, default=str),
                        campos.get("status_atendimento"),  # valor original do Koepe (informativo)
                        "PENDENTE",                         # STATUS_MONITOR: controlado pelo webapp
                        None,
                        "00:00",
                        "NAO",
                        None,
                        _now_str(),
                        _now_str(),
                    ),
                )
                add_comentario(
                    conn, id_atendimento, "Sistema", tipo="automatico",
                    texto=f"Serviço chegou em {_now_str()}",
                )
                novos += 1
            else:
                conn.execute(
                    """UPDATE servicos SET
                        data_inicio=?, tipo_servico=?, urgente=?, solicitante=?,
                        local_origem=?, local_destino=?, percurso=?, observacoes=?,
                        placa=?, motorista=?, telefone_contato=?, campos_extra=?,
                        status_atendimento=?, atualizado_em=?
                    WHERE id_atendimento=?""",
                    (
                        campos.get("data_inicio"),
                        campos.get("tipo_servico"),
                        campos.get("urgente"),
                        campos.get("solicitante"),
                        campos.get("local_origem"),
                        campos.get("local_destino"),
                        campos.get("percurso"),
                        campos.get("observacoes"),
                        campos.get("placa"),
                        campos.get("motorista"),
                        campos.get("telefone_contato"),
                        json.dumps(extras, ensure_ascii=False, default=str),
                        campos.get("status_atendimento"),
                        _now_str(),
                        id_atendimento,
                    ),
                )
                atualizados += 1
    return {"novos": novos, "atualizados": atualizados}


def import_usuarios_excel(caminho=None):
    caminho = caminho or config.ARQ_USUARIOS
    df = pd.read_excel(caminho)
    with get_connection() as conn:
        for _, row in df.iterrows():
            campos = {config.COLUNAS_USUARIOS.get(c, c): v for c, v in row.items()}
            nome = campos.get("nome")
            if not nome or (isinstance(nome, float) and pd.isna(nome)):
                continue
            for k in ("email", "cpf", "telefone", "filial", "grupo", "eh_programador"):
                if isinstance(campos.get(k), float) and pd.isna(campos.get(k)):
                    campos[k] = None
            conn.execute(
                """INSERT INTO usuarios (nome, email, cpf, telefone, filial, grupo, eh_programador)
                VALUES (?,?,?,?,?,?,?)
                ON CONFLICT(nome) DO UPDATE SET
                    email=excluded.email, cpf=excluded.cpf, telefone=excluded.telefone,
                    filial=excluded.filial, grupo=excluded.grupo,
                    eh_programador=excluded.eh_programador""",
                (
                    str(nome), campos.get("email"), campos.get("cpf"),
                    campos.get("telefone"), campos.get("filial"),
                    campos.get("grupo"), campos.get("eh_programador"),
                ),
            )


def import_status_excel(caminho=None):
    caminho = caminho or config.ARQ_STATUS
    df = pd.read_excel(caminho)
    with get_connection() as conn:
        for _, row in df.iterrows():
            campos = {config.COLUNAS_STATUS.get(c, c): v for c, v in row.items()}
            if not campos.get("status"):
                continue
            conn.execute(
                "INSERT INTO status_opcoes (status, descricao) VALUES (?,?) "
                "ON CONFLICT(status) DO UPDATE SET descricao=excluded.descricao",
                (campos.get("status"), campos.get("descricao")),
            )


def importar_tudo():
    r_serv = import_servicos_excel()
    import_usuarios_excel()
    import_status_excel()
    return r_serv


# ---------------------------------------------------------------------------
# Consultas para a interface
# ---------------------------------------------------------------------------
def listar_servicos():
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM servicos ORDER BY criado_em DESC"
        ).fetchall()
        return [dict(r) for r in rows]


def obter_servico(id_atendimento):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM servicos WHERE id_atendimento = ?", (id_atendimento,)
        ).fetchone()
        # Mais recente primeiro (item pedido pelo usuário).
        comentarios = conn.execute(
            "SELECT * FROM comentarios WHERE servico_id = ? ORDER BY data_hora DESC, id DESC",
            (id_atendimento,),
        ).fetchall()
        return (dict(row) if row else None), [dict(c) for c in comentarios]


def listar_usuarios(grupo=None):
    with get_connection() as conn:
        if grupo:
            rows = conn.execute(
                "SELECT * FROM usuarios WHERE grupo = ? ORDER BY nome", (grupo,)
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM usuarios ORDER BY nome").fetchall()
        return [dict(r) for r in rows]


def listar_programadores():
    """Usuários marcados com PROGRAMADOR = 'SIM' na planilha de Usuários."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM usuarios WHERE eh_programador = ? ORDER BY nome",
            (config.VALOR_PROGRAMADOR_SIM,),
        ).fetchall()
        return [dict(r) for r in rows]


def listar_status():
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM status_opcoes ORDER BY status").fetchall()
        return [dict(r) for r in rows]


def servicos_sem_programador():
    """Item 7: serviços sem Programador vinculado. Não filtramos pelo
    'Status do atendimento' original do Koepe (seus valores variam e não
    são controlados por nós) — só pelo campo Programador em branco, como
    pede a especificação."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id_atendimento, solicitante, tipo_servico, percurso, criado_em FROM servicos "
            "WHERE (programador IS NULL OR programador = '')"
        ).fetchall()
        return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Regras de negócio (itens 7, 8 e 9 do documento)
# ---------------------------------------------------------------------------
def vincular_programador(id_atendimento, programador):
    """Item 8/9: vincula um Programador ao serviço, grava log automático,
    marca programador_vinculado=SIM, grava data_hora_vinculo e muda o
    STATUS_MONITOR (o status controlado pelo webapp, separado do 'Status
    do atendimento' original do Koepe) para ABERTO."""
    agora = _now_str()
    with get_connection() as conn:
        conn.execute(
            """UPDATE servicos SET
                programador=?, programador_vinculado='SIM', data_hora_vinculo=?,
                status_monitor='ABERTO', atualizado_em=?
            WHERE id_atendimento=?""",
            (programador, agora, agora, id_atendimento),
        )
        add_comentario(
            conn, id_atendimento, "Sistema", tipo="automatico",
            texto=f"Solic sendo atendida por: {programador} {agora}",
        )


def reverter_vinculo(id_atendimento):
    """Reverte o vínculo do Programador com o serviço: remove o Programador,
    volta STATUS_MONITOR para PENDENTE (o serviço reaparece no banner de
    'aguardando Programador') e limpa data_hora_vinculo (o cálculo de tempo
    de resposta volta a rodar sozinho, como se ainda não tivesse sido
    atendido). Usado tanto para excluir o vínculo quanto como primeiro passo
    para trocar de Programador (depois é só vincular outro nome normalmente).
    Grava um log automático em Comentários com o nome de quem estava
    vinculado antes da reversão."""
    agora = _now_str()
    with get_connection() as conn:
        row = conn.execute(
            "SELECT programador FROM servicos WHERE id_atendimento = ?",
            (id_atendimento,),
        ).fetchone()
        programador_anterior = (row["programador"] if row else None) or "(sem nome)"
        conn.execute(
            """UPDATE servicos SET
                programador=NULL, programador_vinculado='NAO', data_hora_vinculo=NULL,
                status_monitor='PENDENTE', atualizado_em=?
            WHERE id_atendimento=?""",
            (agora, id_atendimento),
        )
        add_comentario(
            conn, id_atendimento, "Sistema", tipo="automatico",
            texto=f"Vínculo com {programador_anterior} revertido em {agora}",
        )


def adicionar_comentario_manual(id_atendimento, autor, texto):
    with get_connection() as conn:
        add_comentario(conn, id_atendimento, autor, texto=texto, tipo="manual")


def recalcular_tempo_resposta():
    """Item 9 (cálculo de tempo de resposta): enquanto data_hora_vinculo
    estiver em branco, soma o tempo decorrido entre 'Data de início' e
    agora, formata HH:MM e salva em tempo_resposta1."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id_atendimento, data_inicio FROM servicos "
            "WHERE data_hora_vinculo IS NULL OR data_hora_vinculo = ''"
        ).fetchall()
        for row in rows:
            if not row["data_inicio"]:
                continue
            try:
                # As datas na planilha real vêm como texto "DD/MM/AAAA HH:MM"
                # (formato brasileiro), por isso dayfirst=True é obrigatório.
                inicio = pd.to_datetime(row["data_inicio"], dayfirst=True)
            except Exception:
                continue
            delta = datetime.now() - inicio.to_pydatetime()
            total_min = max(int(delta.total_seconds() // 60), 0)
            horas, minutos = divmod(total_min, 60)
            tempo_fmt = f"{horas:02d}:{minutos:02d}"
            conn.execute(
                "UPDATE servicos SET tempo_resposta1=? WHERE id_atendimento=?",
                (tempo_fmt, row["id_atendimento"]),
            )
