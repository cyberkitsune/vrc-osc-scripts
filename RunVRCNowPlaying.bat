@echo off
call UpdateScripts.bat
echo "Installing requirements (be sure to have python installed and in PATH)"
python -m pip install -r VRCNowPlaying/Requirements.txt
python VRCNowPlaying/vrcnowplaying.py
pause