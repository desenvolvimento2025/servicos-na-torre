# Como publicar o "Serviços na Torre" online (Streamlit Community Cloud)

Você já tem conta no GitHub — então só falta criar o repositório deste
projeto nela e conectar o Streamlit Community Cloud (gratuito, login pelo
próprio GitHub). Faça isso uma vez só; depois, atualizar o app publicado é
só rodar um arquivo `.bat` (explicado no final).

> **Sobre os dados**: como decidido, o app publicado vai usar os **dados
> reais** das 3 planilhas. Como a nuvem não enxerga sua pasta do OneDrive,
> cópias dessas planilhas ficam na pasta `dados_nuvem/` deste projeto e
> viajam junto com o código para o GitHub. O arquivo
> `atualizar_dados_nuvem.bat` atualiza essas cópias sempre que você quiser.
>
> **Sobre login**: confirmado anteriormente que o app não deve pedir login
> para quem usa. Isso significa que **qualquer pessoa com o link** vai
> conseguir abrir o app e ver os dados reais (inclusive nome/telefone de
> motorista). Se preferir restringir o acesso mais tarde, o Streamlit Cloud
> tem uma opção de "restringir por e-mail" em
> *App settings > Sharing* — aí quem acessa precisa logar com Google/e-mail
> cadastrado. Não fiz essa restrição por padrão, pois conflita com "sem
> login"; me avise se quiser habilitar depois.

## Passo 1 — Criar o repositório no GitHub

1. Acesse https://github.com e faça login com sua conta.
2. Crie um novo repositório: botão **New repository**.
   - Nome sugerido: `servicos-na-torre`
   - Pode deixar como **Private** (o Streamlit Cloud consegue acessar
     repositórios privados da sua própria conta).
   - Não marque nenhuma opção de "adicionar README" (o projeto já tem um).

## Passo 2 — Enviar o código para o GitHub

Abra o **cmd** dentro da pasta do projeto
(`C:\Users\Guilherme\Desktop\Proj Coml\WEB APP TICKETS`) e rode, uma vez:

```bat
cd "C:\Users\Guilherme\Desktop\Proj Coml\WEB APP TICKETS"
git init
git add .
git commit -m "Versao inicial"
git branch -M main
git remote add origin https://github.com/SEU_USUARIO/servicos-na-torre.git
git push -u origin main
```

Troque `SEU_USUARIO` pelo seu usuário do GitHub (o GitHub mostra esse
comando exato na tela do repositório recém-criado, em "…or push an
existing repository from the command line"). Se pedir login, use sua
conta do GitHub.

## Passo 3 — Publicar no Streamlit Community Cloud

1. Acesse https://share.streamlit.io e faça login **com sua conta do
   GitHub** (botão "Continue with GitHub").
2. Clique em **New app** (ou **Create app**).
3. Escolha:
   - Repository: `SEU_USUARIO/servicos-na-torre`
   - Branch: `main`
   - Main file path: `app.py`
4. Clique em **Deploy**. Aguarde alguns minutos — o Streamlit instala o
   que está em `requirements.txt` e sobe o app sozinho.
5. Ao terminar, você recebe uma URL pública, algo como
   `https://servicos-na-torre-xxxx.streamlit.app` — esse é o link para
   compartilhar/testar.

## Passo 4 — Manter os dados atualizados na nuvem

Sempre que quiser que o app publicado reflita os dados mais recentes das
planilhas reais, dê **duplo clique** em:

```
atualizar_dados_nuvem.bat
```

(dentro da pasta do projeto). Ele copia as 3 planilhas do OneDrive para
`dados_nuvem/` e envia para o GitHub — o Streamlit Cloud percebe sozinho
e atualiza o app publicado em 1 a 2 minutos. Não precisa fazer mais nada.

## Passo 5 — Receber atualizações de código

Toda vez que eu enviar uma nova versão do código para esta pasta, dê
duplo clique em:

```
publicar_codigo.bat
```

Isso envia o código atualizado para o GitHub, e o Streamlit Cloud atualiza
o app publicado sozinho.

## Observações

- O app publicado na nuvem **não roda mais localmente pela sua máquina** —
  ele fica sempre ativo nos servidores do Streamlit Cloud, então já resolve
  o item pendente de "manter o app sempre ativo" *para esta versão de
  testes*. Para uma versão definitiva/interna da empresa, ainda vale
  avaliar depois se querem um servidor próprio.
- O plano gratuito do Streamlit Community Cloud é público (qualquer link
  pode ser acessado por quem o tiver) e tem limite de recursos — está OK
  para fase de testes; se decidirem seguir com isso em produção, cabe
  reavaliar um plano pago ou hospedagem própria.
