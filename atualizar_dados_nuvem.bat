@echo off
chcp 65001 >nul
setlocal

rem ---------------------------------------------------------------------
rem Copia as 3 planilhas REAIS do OneDrive para a pasta "dados_nuvem" do
rem projeto e envia (git push) para o GitHub. O Streamlit Community Cloud
rem detecta o push sozinho e atualiza o app publicado com os dados novos
rem em 1 a 2 minutos. Rode este arquivo (duplo clique) sempre que quiser
rem atualizar os dados do app publicado na nuvem.
rem ---------------------------------------------------------------------

set ORIGEM=C:\Users\Guilherme\OneDrive - EXPRESSO PREDILETO\Aplicativos\SOLICIT_TORRE
set DESTINO=%~dp0dados_nuvem

echo Copiando planilhas reais para dados_nuvem...
copy /Y "%ORIGEM%\solicitações -crane.xlsx" "%DESTINO%\solicitações -crane.xlsx"
copy /Y "%ORIGEM%\Usuarios.xlsx" "%DESTINO%\Usuarios.xlsx"
copy /Y "%ORIGEM%\Status.xlsx" "%DESTINO%\Status.xlsx"

echo.
echo Enviando para o GitHub (isso atualiza o app publicado na nuvem)...
git add dados_nuvem
git commit -m "Atualiza dados para a nuvem"
git push

echo.
echo Pronto! Em 1 a 2 minutos o app publicado no Streamlit Cloud aparece
echo com os dados atualizados.
pause
