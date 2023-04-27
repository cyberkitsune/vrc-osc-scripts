@echo off
call UpdateScripts.bat
echo [%~n0] Installing requirements (be sure to have python installed and in PATH)
python -m pip install -r VRCSubs/Requirements.txt -q
python VRCSubs/vrcsubs.py
pause