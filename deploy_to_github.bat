@echo off
echo ========================================
echo Deploiement du projet Edu-ECG sur GitHub
echo ========================================
echo.

REM Initialiser Git
echo [1/7] Initialisation de Git...
git init

REM Configurer Git
echo.
echo [2/7] Configuration de Git...
git config user.name "Gregoire Massoullie"
git config user.email "gregoire.massoullie@orange.fr"

REM Ajouter tous les fichiers
echo.
echo [3/7] Ajout de tous les fichiers...
git add .

REM Faire un commit (même si déjà commité)
echo.
echo [4/7] Commit des modifications...
git commit -m "Force update: écrase la version GitHub avec la version locale" || echo "Aucun changement à commiter"

REM Définir le remote (remplacez l'URL si besoin)
echo.
echo [5/7] Configuration du remote GitHub...
git remote remove origin 2>nul
git remote add origin https://github.com/EPCASE/edu-ecg.git
git branch -M main

REM Forcer le push (⚠️ cela écrase la branche distante)
echo.
echo [6/7] Force push vers GitHub...
echo ========================================
echo IMPORTANT: Authentification GitHub
echo ========================================
echo.
echo GitHub necessite un token d'acces personnel.
echo Si vous n'en avez pas :
echo 1. Allez sur GitHub.com
echo 2. Settings -^> Developer settings -^> Personal access tokens
echo 3. Generate new token avec les permissions 'repo'
echo 4. Copiez le token et utilisez-le comme mot de passe
echo.
echo Appuyez sur une touche pour continuer avec le push force...
pause > nul

git push --force origin main

echo.
echo ========================================
echo Deploiement termine !
echo ========================================
echo.
echo Pour les prochaines modifications :
echo   git add .
echo   git commit -m "Description des changements"
echo   git push
echo.
pause

:: filepath: c:\Users\Administrateur\Desktop\ECG lecture\deploy_scalingo.bat
@echo off
echo ========================================
echo Deploiement Edu-ECG sur Scalingo
echo ========================================

:: Vérifier que Scalingo CLI est installé
where scalingo >nul 2>nul
if errorlevel 1 (
    echo [ERREUR] Scalingo CLI n'est pas installee.
    echo Telechargez-la ici : https://cli.scalingo.com/
    pause
    exit /b 1
)

:: Demander l'URL du remote Scalingo si non existant
git remote get-url scalingo >nul 2>nul
if errorlevel 1 (
    echo.
    set /p APPURL="Entrez l'URL du remote Scalingo (ex: git@scalingo.com:mon-app.git) : "
    git remote add scalingo %APPURL%
)

:: Ajouter les fichiers Scalingo essentiels
echo.
echo [1/3] Ajout des fichiers de configuration Scalingo...
if not exist ".python-version" echo 3.11 > .python-version
if not exist "Procfile" echo web: streamlit run frontend/app.py --server.port \$PORT --server.address 0.0.0.0 > Procfile
if not exist ".streamlit" mkdir .streamlit
if not exist ".streamlit\config.toml" (
    echo [server]> .streamlit\config.toml
    echo headless = true>> .streamlit\config.toml
    echo port = \$PORT>> .streamlit\config.toml
    echo enableCORS = false>> .streamlit\config.toml
    echo.>> .streamlit\config.toml
    echo [browser]>> .streamlit\config.toml
    echo serverAddress = "0.0.0.0">> .streamlit\config.toml
)

git add .python-version Procfile .streamlit/config.toml
git commit -m "Ajout fichiers config Scalingo" || echo "Aucun changement a commiter"

:: Push vers Scalingo
echo.
echo [2/3] Push vers Scalingo...
git push scalingo main

echo.
echo [3/3] Deploiement termine !
echo.
pause
echo streamlit run frontend/app.py
echo ```
echo.
echo ## 👥 Auteur
echo.
echo Gregoire Massoullie - gregoire.massoullie@orange.fr
echo.
echo ## 📄 Licence
echo.
echo MIT License
) > README.md

REM Créer requirements.txt
echo.
echo [5/8] Creation du fichier requirements.txt...
(
echo streamlit^>=1.28.0
echo pandas^>=2.0.0
echo numpy^>=1.24.0
echo Pillow^>=10.0.0
echo rdflib^>=7.0.0
echo bcrypt^>=4.0.0
) > requirements.txt

REM Ajouter tous les fichiers
echo.
echo [6/8] Ajout de tous les fichiers...
git add .

REM Faire le premier commit
echo.
echo [7/8] Creation du premier commit...
git commit -m "Initial commit - Edu-ECG platform"

REM Ajouter le remote et pousser
echo.
echo [8/8] Connexion a GitHub et envoi...
git remote add origin https://github.com/EPCASE/edu-ecg.git
git branch -M main

echo.
echo ========================================
echo IMPORTANT: Authentification GitHub
echo ========================================
echo.
echo GitHub necessite un token d'acces personnel.
echo Si vous n'en avez pas :
echo 1. Allez sur GitHub.com
echo 2. Settings -^> Developer settings -^> Personal access tokens
echo 3. Generate new token avec les permissions 'repo'
echo 4. Copiez le token et utilisez-le comme mot de passe
echo.
echo Appuyez sur une touche pour continuer avec le push...
pause > nul

git push -u origin main

echo.
echo ========================================
echo Deploiement termine !
echo ========================================
echo.
echo Pour les prochaines modifications :
echo   git add .
echo   git commit -m "Description des changements"
echo   git push
echo.
pause

:: filepath: c:\Users\Administrateur\Desktop\ECG lecture\deploy_scalingo.bat
@echo off
echo ========================================
echo Deploiement Edu-ECG sur Scalingo
echo ========================================

:: Vérifier que Scalingo CLI est installé
where scalingo >nul 2>nul
if errorlevel 1 (
    echo [ERREUR] Scalingo CLI n'est pas installee.
    echo Telechargez-la ici : https://cli.scalingo.com/
    pause
    exit /b 1
)

:: Demander l'URL du remote Scalingo si non existant
git remote get-url scalingo >nul 2>nul
if errorlevel 1 (
    echo.
    set /p APPURL="Entrez l'URL du remote Scalingo (ex: git@scalingo.com:mon-app.git) : "
    git remote add scalingo %APPURL%
)

:: Ajouter les fichiers Scalingo essentiels
echo.
echo [1/3] Ajout des fichiers de configuration Scalingo...
if not exist ".python-version" echo 3.11 > .python-version
if not exist "Procfile" echo web: streamlit run frontend/app.py --server.port \$PORT --server.address 0.0.0.0 > Procfile
if not exist ".streamlit" mkdir .streamlit
if not exist ".streamlit\config.toml" (
    echo [server]> .streamlit\config.toml
    echo headless = true>> .streamlit\config.toml
    echo port = \$PORT>> .streamlit\config.toml
    echo enableCORS = false>> .streamlit\config.toml
    echo.>> .streamlit\config.toml
    echo [browser]>> .streamlit\config.toml
    echo serverAddress = "0.0.0.0">> .streamlit\config.toml
)

git add .python-version Procfile .streamlit/config.toml
git commit -m "Ajout fichiers config Scalingo" || echo "Aucun changement a commiter"

:: Push vers Scalingo
echo.
echo [2/3] Push vers Scalingo...
git push scalingo main

echo.
echo [3/3] Deploiement termine !
echo.
pause
