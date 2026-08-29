"""
Gera planilhas Excel de EXEMPLO (dados fictícios), com a MESMA estrutura de
colunas das planilhas reais da pasta OneDrive, para testar o webapp sem
mexer nos arquivos de produção.

Uso:
    python gerar_exemplos.py

Gera em ./data/entrada/:
    - solicitações -crane.xlsx   (planilha "Serviços" que chega a cada 30 min)
    - Usuarios.xlsx
    - Status.xlsx

Para o app usar esta pasta em vez da pasta real do OneDrive, defina antes
de rodar:
    set SERVICOS_TORRE_PASTA=%cd%\\data\\entrada        (cmd do Windows)
"""
import os
import sys
from datetime import timedelta
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from src import tempo  # noqa: E402  (horário de Brasília, ver src/tempo.py)

BASE = os.path.join(os.path.dirname(__file__), "data", "entrada")
os.makedirs(BASE, exist_ok=True)

agora = tempo.agora()


def fmt(dt):
    return dt.strftime("%d/%m/%Y %H:%M")  # mesmo formato da planilha real


# ---------------------------------------------------------------------------
# Planilha "solicitações -crane" -> alimenta a tabela "Serviços"
# Aqui só incluímos as colunas usadas pelo app (grade + regras). Na planilha
# real existem ~90 colunas do sistema Koepe; todas as extras são preservadas
# automaticamente na tela de detalhe, mapeadas ou não.
# ---------------------------------------------------------------------------
servicos = pd.DataFrame([
    {
        "Id do atendimento": 1001,
        "Data de início": fmt(agora - timedelta(hours=2, minutes=10)),
        "Tipo do serviço": "Guincho",
        "Urgente": "Sim",
        "Solicitante": "João Mendes",
        "Local de origem": "Filial Barueri",
        "Local de destino": "Filial Osasco",
        "Percurso": "Rodovia Castello Branco km 21",
        "Status do atendimento": "Pendente",
        "Observações do cliente": "Veículo com pane elétrica",
        "Placa": "ABC1D23",
        "Motorista": "Carlos Silva",
        "Telefone do motorista": "(11) 98888-1111",
    },
    {
        "Id do atendimento": 1002,
        "Data de início": fmt(agora - timedelta(minutes=40)),
        "Tipo do serviço": "Munck",
        "Urgente": "Não",
        "Solicitante": "Maria Souza",
        "Local de origem": "CD Cajamar",
        "Local de destino": "Cliente Alphaville",
        "Percurso": "Rodovia dos Bandeirantes km 32",
        "Status do atendimento": "Pendente",
        "Observações do cliente": "Descarga de carga paletizada",
        "Placa": "XYZ9K87",
        "Motorista": "Pedro Lima",
        "Telefone do motorista": "(11) 97777-2222",
    },
    {
        "Id do atendimento": 1003,
        "Data de início": fmt(agora - timedelta(minutes=5)),
        "Tipo do serviço": "Reboque",
        "Urgente": "Sim",
        "Solicitante": "Ana Paula",
        "Local de origem": "BR-116 km 210",
        "Local de destino": "Pátio Predileto SP",
        "Percurso": "BR-116 sentido Curitiba",
        "Status do atendimento": "Pendente",
        "Observações do cliente": "Pneu estourado",
        "Placa": "JKL4M56",
        "Motorista": "Roberto Alves",
        "Telefone do motorista": "(11) 96666-3333",
    },
])
servicos.to_excel(os.path.join(BASE, "solicitações -crane.xlsx"), index=False)

# ---------------------------------------------------------------------------
# Planilha "Usuarios" -> tabela "Usuários" (menu secundário)
# Coluna PROGRAMADOR = SIM/NAO -> quem aparece para ser vinculado a um serviço.
# ---------------------------------------------------------------------------
usuarios = pd.DataFrame([
    {"NOME": "Guilherme Rocha", "E-MAIL": "guilherme.rocha@expressopredileto.com.br", "CPF": None, "TELEFONE": None, "FILIAL": "MACAÉ", "GRUPO": "Torre", "PROGRAMADOR": "SIM"},
    {"NOME": "Fernanda Dias", "E-MAIL": "fernanda.dias@expressopredileto.com.br", "CPF": None, "TELEFONE": None, "FILIAL": "MACAÉ", "GRUPO": "Torre", "PROGRAMADOR": "SIM"},
    {"NOME": "Rafael Nunes", "E-MAIL": "rafael.nunes@expressopredileto.com.br", "CPF": None, "TELEFONE": None, "FILIAL": "MACAÉ", "GRUPO": "Torre", "PROGRAMADOR": "SIM"},
    {"NOME": "Camila Torres", "E-MAIL": "camila.torres@expressopredileto.com.br", "CPF": None, "TELEFONE": None, "FILIAL": "MACAÉ", "GRUPO": "Administrador", "PROGRAMADOR": "NAO"},
])
usuarios.to_excel(os.path.join(BASE, "Usuarios.xlsx"), index=False)

# ---------------------------------------------------------------------------
# Planilha "Status" -> tabela "Status" (menu secundário)
# ---------------------------------------------------------------------------
status = pd.DataFrame([
    {"STATUS": "PENDENTE"},
    {"STATUS": "ABERTO"},
])
status.to_excel(os.path.join(BASE, "Status.xlsx"), index=False)

print(f"Planilhas de exemplo geradas em: {BASE}")
