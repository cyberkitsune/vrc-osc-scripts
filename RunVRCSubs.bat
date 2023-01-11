@echo off
call UpdateScripts.bat
echo "Installing requirements (be sure to have python installed and in PATH)"
pip3 install -r VRCSubs/Requirements.txt
python3 VRCSubs/vrcsubs.py
pause