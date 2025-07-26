@echo off 
echo Envoi vers GitHub... 
set PATH=%PATH%;C:\Program Files\Git\bin 
cd /d "c:\Users\Administrateur\Desktop\ECG lecture" 
git remote add origin https://github.com/EPCASE/edu-ecg.git 
git push -u origin main 
echo. 
echo ======================================== 
echo    SUCCES ! Votre projet est sur GitHub 
echo ======================================== 
echo Votre projet est maintenant disponible a : 
echo https://github.com/EPCASE/edu-ecg 
echo. 
pause 
