@Echo Off
:_Start
echo "Normal start"
Start /W TPAudioMixer.exe -l log.txt
set ranOnce = true
 
:_runbackup
if ranOnce == false echo "Start program again and load shortid" & Start /W TPAudioMixer.exe --loadShortid -l log.txt

echo %errorlevel%
if NOT %errorlevel% == 1 set ranOnce = false & Goto _runbackup 