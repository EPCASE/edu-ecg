@echo off
echo ========================================
echo    SETUP GITHUB POUR EDU-ECG EPCASE
echo ========================================
echo.

REM Ajouter Git au PATH
set PATH=%PATH%;C:\Program Files\Git\bin

REM Se placer dans le bon dossier
cd /d "c:\Users\Administrateur\Desktop\ECG lecture"

echo 1. Configuration Git...
git config --global user.name "EPCASE"
git config --global user.email "gregoire.massoullie@orange.fr"

echo 2. Initialisation du depot Git...
git init

echo 3. Ajout de tous les fichiers...
git add .

echo 4. Premier commit...
git commit -m "Initial commit - Plateforme Edu-ECG EPCASE"

echo 5. Creation de la branche main...
git branch -M main

echo.
echo ========================================
echo    PREPARATION TERMINEE !
echo ========================================
echo.
echo Maintenant, 2 etapes simples :
echo.
echo ETAPE 1 : Creer le depot sur GitHub.com
echo   1. Ouvrez votre navigateur
echo   2. Allez sur https://github.com
echo   3. Connectez-vous a votre compte GitHub
echo   4. Cliquez sur le bouton vert "New" ou le "+" en haut
echo   5. Nom du depot : edu-ecg
echo   6. Description : Plateforme d'enseignement ECG - EPCASE
echo   7. Laissez Public ou mettez Private selon votre choix
echo   8. NE COCHEZ RIEN d'autre (pas de README, .gitignore, license)
echo   9. Cliquez "Create repository"
echo.
echo ETAPE 2 : Executer le script final
echo   Une fois le depot cree sur GitHub.com :
echo   1. Double-cliquez sur "push_to_github.bat"
echo   2. C'est fini !
echo.
echo ========================================
echo Creation du script final...

REM Créer le script de push automatique
echo @echo off > push_to_github.bat
echo echo Envoi vers GitHub... >> push_to_github.bat
echo set PATH=%%PATH%%;C:\Program Files\Git\bin >> push_to_github.bat
echo cd /d "c:\Users\Administrateur\Desktop\ECG lecture" >> push_to_github.bat
echo git remote add origin https://github.com/EPCASE/edu-ecg.git >> push_to_github.bat
echo git push -u origin main >> push_to_github.bat
echo echo. >> push_to_github.bat
echo echo ======================================== >> push_to_github.bat
echo echo    SUCCES ! Votre projet est sur GitHub >> push_to_github.bat
echo echo ======================================== >> push_to_github.bat
echo echo Votre projet est maintenant disponible a : >> push_to_github.bat
echo echo https://github.com/EPCASE/edu-ecg >> push_to_github.bat
echo echo. >> push_to_github.bat
echo pause >> push_to_github.bat

echo Script final cree : push_to_github.bat
echo.
echo Appuyez sur une touche pour continuer...
pause
