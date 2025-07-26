@echo off
echo ========================================
echo   Edu-CG avec Authentification
echo ========================================
echo.
echo Comptes de demonstration disponibles :
echo - Etudiant : etudiant_demo / etudiant123
echo - Expert   : expert_demo / expert123
echo - Admin    : admin / admin123
echo.
echo Lancement de l'application...
echo URL: http://localhost:8501
echo.

python launch_auth.py

echo.
echo Application arretee.
pause
