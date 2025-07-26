@echo off
echo ========================================
echo Configuration pour Heroku
echo ========================================
echo.

REM Créer .python-version
echo 3.11 > .python-version

REM Créer Procfile
echo web: streamlit run frontend/app.py --server.port $PORT --server.address 0.0.0.0 > Procfile

REM Créer le dossier .streamlit si nécessaire
if not exist ".streamlit" mkdir .streamlit

REM Créer config.toml
(
echo [server]
echo headless = true
echo port = $PORT
echo enableCORS = false
echo.
echo [browser]
echo serverAddress = "0.0.0.0"
) > .streamlit\config.toml

REM Créer runtime.txt
echo python-3.11.13 > runtime.txt

REM Ajouter et commiter les changements
git add .python-version Procfile .streamlit/config.toml runtime.txt
git commit -m "Add Heroku configuration files"

echo.
echo ========================================
echo Configuration terminée !
echo ========================================
echo.
echo Maintenant, exécutez :
echo   git push heroku main
echo.
pause
