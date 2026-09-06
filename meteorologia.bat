@echo off
:: 1. Entra na pasta do seu projeto
cd /d "C:\meteorologia"

:: 2. Ativa o ambiente virtual (ajuste se o nome não for 'venv')
call venv\Scripts\activate

:: 3. Executa o seu código python
python -m main

:: 4. Mantém a janela aberta para você ver erros ou saídas
pause