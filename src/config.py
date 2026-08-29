"""
Configurações do projeto Serviços na Torre.

Ajustado a partir das planilhas REAIS encontradas em:
C:\\Users\\Guilherme\\OneDrive - EXPRESSO PREDILETO\\Aplicativos\\SOLICIT_TORRE
"""
import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "data", "servicos_na_torre.db")

# -----------------------------------------------------------------------
# Pasta de entrada (onde o app procura as planilhas Excel)
# -----------------------------------------------------------------------
# Ordem de escolha da pasta:
# 1) Variável de ambiente SERVICOS_TORRE_PASTA, se definida (útil para
#    testar com planilhas de exemplo ou apontar outro lugar manualmente).
# 2) A pasta real do OneDrive do Guilherme, se ela existir neste
#    computador (é o caso quando o app roda local, na máquina dele).
# 3) A pasta 'dados_nuvem' dentro do próprio projeto — é para onde vão
#    CÓPIAS das 3 planilhas reais, versionadas no GitHub junto com o
#    código, para o app conseguir ler dados reais quando publicado no
#    Streamlit Community Cloud (que não tem acesso ao OneDrive local).
#    Ver 'sync_dados_nuvem.py' / 'atualizar_dados_nuvem.bat' para manter
#    essas cópias atualizadas.
_PASTA_ONEDRIVE = r"C:\Users\Guilherme\OneDrive - EXPRESSO PREDILETO\Aplicativos\SOLICIT_TORRE"
_PASTA_NUVEM = os.path.join(BASE_DIR, "dados_nuvem")

if os.environ.get("SERVICOS_TORRE_PASTA"):
    PASTA_PLANILHAS = os.environ["SERVICOS_TORRE_PASTA"]
elif os.path.isdir(_PASTA_ONEDRIVE):
    PASTA_PLANILHAS = _PASTA_ONEDRIVE
else:
    PASTA_PLANILHAS = _PASTA_NUVEM

# Nomes EXATOS dos arquivos reais (cuidado: o arquivo de serviços tem um
# espaço antes do hífen e acentos: "solicitações -crane.xlsx").
ARQ_SERVICOS = os.path.join(PASTA_PLANILHAS, "solicitações -crane.xlsx")
ARQ_USUARIOS = os.path.join(PASTA_PLANILHAS, "Usuarios.xlsx")
ARQ_STATUS = os.path.join(PASTA_PLANILHAS, "Status.xlsx")

# -----------------------------------------------------------------------
# Intervalos das rotinas (em segundos) - conforme especificação
# -----------------------------------------------------------------------
INTERVALO_IMPORTACAO_SEGUNDOS = 30 * 60   # item 6: a cada 30 minutos
INTERVALO_TEMPO_RESPOSTA_SEGUNDOS = 60    # item 9: a cada 1 minuto
INTERVALO_BANNER_SEGUNDOS = 5 * 60        # item 7: banner volta a cada 5 minutos

# -----------------------------------------------------------------------
# Mapeamento das colunas da planilha real "solicitações -crane.xlsx"
# (aba "Solicitações CRANE", 90 colunas originais do sistema Koepe +
# "Primeira captura" / "Última atualização", alimentada por uma automação
# separada que já roda de hora em hora neste mesmo computador).
#
# chave = nome da coluna no Excel  ->  valor = nome do campo interno
#
# Só mapeamos aqui os campos usados na grade principal e nas regras de
# negócio. TODAS as demais colunas (as outras ~80, incluindo "Primeira
# captura"/"Última atualização") são preservadas automaticamente na tela
# de detalhe do serviço, na ordem em que aparecem na planilha — nenhuma
# informação é perdida mesmo sem estar mapeada aqui.
# -----------------------------------------------------------------------
COLUNAS_SERVICOS = {
    "Id do atendimento": "id_atendimento",
    "Data de início": "data_inicio",
    "Tipo do serviço": "tipo_servico",
    "Urgente": "urgente",
    "Solicitante": "solicitante",
    "Local de origem": "local_origem",
    "Local de destino": "local_destino",
    "Percurso": "percurso",
    "Observações do cliente": "observacoes",
    "Placa": "placa",
    "Motorista": "motorista",
    "Telefone do motorista": "telefone_contato",
    # Status ORIGINAL do sistema Koepe (ex: "Pendente", "Em Aberto",
    # "Cancelado"...). É só informativo — não é o que controla o fluxo do
    # webapp. Quem controla o fluxo é o STATUS_MONITOR (ver database.py).
    "Status do atendimento": "status_atendimento",
}

# Colunas mostradas na grade principal, nesta ordem exata (item 2 do documento)
COLUNAS_GRADE_PRINCIPAL = [
    ("id_atendimento", "Id do atendimento"),
    ("data_inicio", "Data de início"),
    ("tipo_servico", "Tipo do serviço"),
    ("urgente", "Urgente"),
    ("solicitante", "Solicitante"),
    ("local_origem", "Local de origem"),
    ("local_destino", "Local de destino"),
    ("percurso", "Percurso"),
    ("status_atendimento", "Status do atendimento"),
    ("status_monitor", "STATUS_MONITOR"),
    ("programador", "Programador"),
    ("filial_programador", "Filial"),
]

# Planilha real: aba "Usuários", colunas NOME, E-MAIL, CPF, TELEFONE,
# FILIAL, GRUPO, PROGRAMADOR (coluna adicionada por vocês para marcar
# quem pode ser vinculado como Programador de um serviço; valores
# esperados: "SIM" / "NAO").
COLUNAS_USUARIOS = {
    "NOME": "nome",
    "E-MAIL": "email",
    "CPF": "cpf",
    "TELEFONE": "telefone",
    "FILIAL": "filial",
    "GRUPO": "grupo",
    "PROGRAMADOR": "eh_programador",
}

# Valor da coluna PROGRAMADOR que marca um usuário como elegível a ser
# vinculado a um serviço.
VALOR_PROGRAMADOR_SIM = "SIM"

# Planilha real: aba "Plan1", coluna única STATUS (sem descrição)
COLUNAS_STATUS = {
    "STATUS": "status",
}
