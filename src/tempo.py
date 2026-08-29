"""
Utilitário de data/hora do projeto.

O app deve sempre trabalhar com o horário de Brasília (America/Sao_Paulo),
independentemente do fuso horário do servidor onde o processo está
rodando. Isso importa principalmente quando o app está publicado na nuvem
(Streamlit Community Cloud): o servidor normalmente roda em UTC, então
usar datetime.now() puro gravaria os horários (data_hora_vinculo,
comentários, "há Xh Ymin sem Programador" etc.) 3 horas adiantados em
relação ao horário real de Brasília. Rodando localmente no Brasil, o
resultado de agora() é o mesmo de antes (já que a máquina já está no
fuso de Brasília).
"""
from datetime import datetime
from zoneinfo import ZoneInfo

_FUSO_BRASILIA = ZoneInfo("America/Sao_Paulo")


def agora():
    """Horário atual de Brasília, como datetime 'naive' (sem timezone
    anexado) — para poder ser comparado/formatado do mesmo jeito que o
    resto do código, que já trabalha com datas sem timezone (as datas das
    planilhas do Koepe também são texto puro, sem timezone)."""
    return datetime.now(_FUSO_BRASILIA).replace(tzinfo=None)
