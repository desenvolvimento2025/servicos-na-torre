# Serviços na Torre (protótipo)

Webapp de ticket de atendimento e monitoramento de serviços logísticos,
para a Expresso Predileto. Este é um **protótipo funcional** construído em
Python + Streamlit, para validarmos juntos as regras de negócio antes de
ir para produção.

## Como rodar (via cmd / prompt de comando)

Requer Python 3.10+ instalado.

```bat
cd servicos_na_torre
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

streamlit run app.py
```

Rodando assim (sem definir `SERVICOS_TORRE_PASTA`), o app já lê direto da
pasta real do OneDrive
(`C:\Users\Guilherme\OneDrive - EXPRESSO PREDILETO\Aplicativos\SOLICIT_TORRE`),
que é onde as 3 planilhas reais já estão. Rode isso no computador do
Guilherme, onde essa pasta existe de fato.

O navegador abre automaticamente em `http://localhost:8501`. Para acessar
de outro dispositivo (celular) na mesma rede Wi-Fi, use o endereço de rede
que o Streamlit mostra no terminal (algo como `http://192.168.x.x:8501`).

Para testar com dados FICTÍCIOS em vez da pasta real (ex: rodando fora do
computador do Guilherme), gere exemplos e aponte a pasta antes de subir o
app:

```bat
python gerar_exemplos.py
set SERVICOS_TORRE_PASTA=%cd%\data\entrada
streamlit run app.py
```

## O que já está implementado (a partir da especificação)

- Tabela **Serviços** (repositório em SQLite local, `data/servicos_na_torre.db`)
  com os campos extras `Status_monitor`, `Programador`, `Tempo_resposta1`,
  `Programador_vinculado`, `Data_hora_vinculo`.
- Grade principal com as 11 colunas na ordem especificada — inclui as
  DUAS colunas de status lado a lado: `Status do atendimento` (o status
  original do sistema Koepe, só informativo) e `STATUS_MONITOR` (o status
  que o próprio webapp controla, com os valores `PENDENTE`/`ABERTO` da
  planilha `Status.xlsx`).
- Tela de detalhe com os demais campos + seção **Comentários** (logs
  automáticos e manuais).
- Menus discretos de **Usuários** e **Status** na barra lateral.
- Importação da planilha `solicitações -crane.xlsx` a cada 30 minutos
  (rotina em background), criando novos serviços com `STATUS_MONITOR =
  PENDENTE` e preservando os campos controlados pelo webapp em
  atualizações.
- **Sem login/autenticação** — qualquer pessoa pode abrir o webapp,
  confirmado por você. Só é pedido para selecionar o próprio nome (lista
  filtrada por `PROGRAMADOR = SIM` na planilha de Usuários) para
  identificar comentários e vínculos.
- Banner de "serviço sem Programador", que reaparece a cada 5 minutos até
  todos os serviços pendentes terem um Programador.
- Ao vincular um Programador: log automático, `Programador_vinculado=SIM`,
  `Data_hora_vinculo` preenchida, `STATUS_MONITOR` muda para `ABERTO`.
- Recalculo de `Tempo_resposta1` (HH:MM) a cada 1 minuto enquanto o
  serviço não tiver Programador vinculado.

## Fonte de dados real (já conferida)

Por padrão (`src/config.py`) o app já lê diretamente da pasta real:

`C:\Users\Guilherme\OneDrive - EXPRESSO PREDILETO\Aplicativos\SOLICIT_TORRE`

As colunas de `Usuarios.xlsx` (NOME, E-MAIL, CPF, TELEFONE, FILIAL, GRUPO),
`Status.xlsx` (coluna única STATUS) e `solicitações -crane.xlsx` (90
colunas do sistema Koepe + `Primeira captura`/`Última atualização`) já
foram lidas e mapeadas em `src/config.py`.

**Descoberta importante**: a planilha `solicitações -crane.xlsx` já é
alimentada por uma automação separada (projeto "SOLICIT_TORRE" no
Cowork, tarefa agendada de hora em hora, documentada em
`Projeto_Solicitacoes_CRANE_Backup_1.md`/`_2.md` na própria pasta), que
extrai os atendimentos do sistema Koepe (Control Tower) via navegador e
mantém a planilha sempre atualizada por upsert. Ou seja, o webapp **não
precisa** buscar dados no Koepe — só precisa ler essa planilha, que já
chega pronta. Isso já está implementado.

**"Programador"**: adicionei a coluna `PROGRAMADOR` (valores `SIM`/`NAO`)
na planilha `Usuarios.xlsx` real, já marcando `SIM` para os 4 usuários do
grupo "Torre" (Diogo, Pricila, Ricardo e um usuário de teste) e `NAO`
para os demais 285. O app usa essa coluna para decidir quem aparece nos
seletores de "Programador responsável". Se algum outro nome também
precisar ser Programador, é só marcar `SIM` na planilha (não precisa
mexer no código).

**`STATUS_MONITOR`**: confirmado — é o campo controlado pelo webapp, que
guarda `PENDENTE` (serviço chegou, sem Programador ainda) ou `ABERTO`
(Programador já vinculado), os dois valores da planilha `Status.xlsx`.
Ele é diferente do `Status do atendimento`, que é o status original do
sistema Koepe e só aparece na tela como informação (não é alterado pelo
webapp).

## Publicar online para testes (Streamlit Community Cloud)

Passo a passo completo em **[`DEPLOY.md`](DEPLOY.md)**. Resumo:

- Foi escolhido publicar na nuvem **com dados reais** (não fictícios).
- Como o Streamlit Community Cloud não acessa o OneDrive local, cópias das
  3 planilhas reais ficam em `dados_nuvem/` e sobem para o GitHub junto
  com o código.
- `atualizar_dados_nuvem.bat` (duplo clique) atualiza essas cópias e
  publica a versão mais recente dos dados.
- `publicar_codigo.bat` (duplo clique) publica atualizações de código.
- **Continua sem login**, como definido — ou seja, qualquer pessoa com o
  link do app publicado consegue ver os dados reais. Isso está detalhado
  (com alternativa opcional de restrição por e-mail do Streamlit Cloud)
  no `DEPLOY.md`.
- Você já tem conta no GitHub — falta só criar o repositório e seguir o
  `DEPLOY.md` (passos 1 a 3) para publicar.

## Simplificações do protótipo (a decidir com você antes da versão final)

1. **Execução contínua e reinício automático**: rodando localmente via
   `streamlit run app.py`, ainda precisaria virar serviço do Windows (ex:
   NSSM ou Task Scheduler) para reiniciar sozinho. **Já resolvido para a
   versão de testes publicada na nuvem** (ver seção acima) — lá o app fica
   sempre ativo nos servidores do Streamlit Cloud, sem depender do seu PC
   ligado.
2. **GitHub**: ver `DEPLOY.md` — passo a passo de criar o repositório e
   publicar.
3. **Dados de teste na planilha de Usuários**: existem linhas como
   "2026 - testes", "2027-testes" e "2028" no grupo Operacional/Vigilante
   — não têm PROGRAMADOR=SIM, então não afetam o app, mas vale uma
   limpeza futura.

## Estrutura

```
servicos_na_torre/
├── app.py                 # interface Streamlit
├── gerar_exemplos.py      # gera planilhas de exemplo p/ teste
├── requirements.txt
├── src/
│   ├── config.py           # caminhos e mapeamento de colunas
│   ├── database.py         # repositório SQLite + importação + regras
│   └── scheduler.py        # rotinas em background (30min / 1min)
└── data/
    ├── entrada/             # planilhas de exemplo (ou reais)
    └── servicos_na_torre.db # banco local (gerado ao rodar)
```
