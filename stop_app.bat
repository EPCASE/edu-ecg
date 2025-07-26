@echo off
echo [STOP] ARRET D'URGENCE EDU-CG
echo ========================
echo.

echo [INFO] Recherche des processus Streamlit/Python...
tasklist /FI "IMAGENAME eq python.exe" /FO TABLE | findstr streamlit
if errorlevel 1 (
    echo [OK] Aucun processus Streamlit detecte
) else (
    echo [WARN] Processus Streamlit detecte, arret en cours...
    taskkill /F /IM python.exe /FI "WINDOWTITLE eq *streamlit*" 2>nul
    if errorlevel 1 (
        echo [FORCE] Arret force de tous les processus Python...
        taskkill /F /IM python.exe 2>nul
    )
    echo [OK] Processus arretes
)

echo.
echo [INFO] Verification du port 8501...
netstat -ano | findstr :8501
if errorlevel 1 (
    echo [OK] Port 8501 libre
) else (
    echo [WARN] Port 8501 encore utilise
    echo [TIP] Redemarrez votre ordinateur si le probleme persiste
)

echo.
echo [DONE] Arret termine
pause
