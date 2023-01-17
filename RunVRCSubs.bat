@echo off
call UpdateScripts.bat
echo "Installing requirements (be sure to have python installed and in PATH)"
python -m pip install -r VRCSubs/Requirements.txt
python VRCSubs/vrcsubs.py
pause