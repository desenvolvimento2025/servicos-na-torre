@echo off
chcp 65001 >nul

rem ---------------------------------------------------------------------
rem Envia as alteracoes de CODIGO desta pasta para o GitHub. Use depois
rem de eu (Claude) mandar uma nova versao do codigo para esta pasta.
rem O Streamlit Community Cloud detecta o push e atualiza o app publicado
rem sozinho, em 1 a 2 minutos.
rem ---------------------------------------------------------------------

echo Enviando as ultimas alteracoes de codigo para o GitHub...
git add .
git commit -m "Atualizacao de codigo"
git push

echo.
echo Pronto! Em 1 a 2 minutos o app publicado no Streamlit Cloud atualiza sozinho.
pause
