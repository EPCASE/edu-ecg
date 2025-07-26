@echo off
echo ========================================
echo Deploiement du projet Edu-ECG sur GitHub
echo ========================================
echo.

REM Initialiser Git
echo [1/8] Initialisation de Git...
git init

REM Configurer Git
echo.
echo [2/8] Configuration de Git...
git config user.name "Gregoire Massoullie"
git config user.email "gregoire.massoullie@orange.fr"

REM Créer .gitignore
echo.
echo [3/8] Creation du fichier .gitignore...
(
echo # Python
echo __pycache__/
echo *.py[cod]
echo *$py.class
echo *.so
echo .Python
echo build/
echo develop-eggs/
echo dist/
echo downloads/
echo eggs/
echo .eggs/
echo lib/
echo lib64/
echo parts/
echo sdist/
echo var/
echo wheels/
echo *.egg-info/
echo .installed.cfg
echo *.egg
echo.
echo # Virtual Environment
echo .conda/
echo venv/
echo env/
echo ENV/
echo.
echo # IDE
echo .vscode/
echo .idea/
echo *.swp
echo *.swo
echo.
echo # OS
echo .DS_Store
echo Thumbs.db
echo.
echo # Project specific
echo data/ecg_cases/
echo data/ecg_sessions/
echo *.log
echo *.tmp
echo temp/
echo.
echo # Streamlit
echo .streamlit/secrets.toml
echo.
echo # Sensitive data
echo users.db
echo *.db
) > .gitignore

REM Créer README.md
echo.
echo [4/8] Creation du fichier README.md...
(
echo # 🫀 Edu-ECG - Plateforme d'apprentissage ECG
echo.
echo Plateforme interactive d'apprentissage de l'electrocardiogramme avec annotation semi-automatique et ontologie medicale.
echo.
echo ## 🚀 Fonctionnalites
echo.
echo - 🧠 **Correction intelligente** basee sur une ontologie de 281 concepts ECG
echo - 📱 **Interface moderne** compatible desktop, tablette et mobile  
echo - 🎓 **Workflow pedagogique** : annotation expert → formation etudiant → evaluation
echo - 📊 **Analytics detailles** avec scoring nuance et suivi de progression
echo - 🔐 **Systeme d'authentification** avec gestion des roles ^(admin, expert, etudiant^)
echo.
echo ## 📦 Installation
echo.
echo 1. Cloner le depot :
echo ```bash
echo git clone https://github.com/EPCASE/edu-ecg.git
echo cd edu-ecg
echo ```
echo.
echo 2. Creer un environnement virtuel :
echo ```bash
echo python -m venv venv
echo # Windows
echo venv\Scripts\activate
echo # Linux/Mac
echo source venv/bin/activate
echo ```
echo.
echo 3. Installer les dependances :
echo ```bash
echo pip install -r requirements.txt
echo ```
echo.
echo ## 🏃‍♂️ Utilisation
echo.
echo Lancer l'application :
echo ```bash
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
