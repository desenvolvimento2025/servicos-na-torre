"""
Rotinas em segundo plano (itens 6 e 9 do documento de requisitos):
  - importar a planilha a cada 30 minutos;
  - recalcular o Tempo_resposta1 a cada 1 minuto.

Streamlit executa o script inteiro a cada interação do usuário, então o
agendador é iniciado apenas UMA VEZ por processo (guarda em variável global
de módulo) usando APScheduler em background thread.
"""
import logging

from apscheduler.schedulers.background import BackgroundScheduler

from . import config, database

log = logging.getLogger("servicos_na_torre.scheduler")

_scheduler = None


def _job_importar():
    try:
        resultado = database.importar_tudo()
        log.info("Importação automática concluída: %s", resultado)
    except Exception:
        log.exception("Falha na importação automática da planilha")


def _job_tempo_resposta():
    try:
        database.recalcular_tempo_resposta()
    except Exception:
        log.exception("Falha ao recalcular Tempo_resposta1")


def iniciar_rotinas_em_background():
    """Idempotente: seguro chamar em toda execução do script Streamlit."""
    global _scheduler
    if _scheduler is not None:
        return _scheduler

    database.init_db()

    scheduler = BackgroundScheduler(daemon=True)
    scheduler.add_job(
        _job_importar, "interval",
        seconds=config.INTERVALO_IMPORTACAO_SEGUNDOS,
        id="importar_planilhas",
    )
    scheduler.add_job(
        _job_tempo_resposta, "interval",
        seconds=config.INTERVALO_TEMPO_RESPOSTA_SEGUNDOS,
        id="tempo_resposta",
    )
    scheduler.start()
    _scheduler = scheduler
    log.info("Rotinas em background iniciadas.")
    return scheduler
