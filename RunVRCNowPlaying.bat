@echo off
call UpdateScripts.bat
echo "Installing requirements (be sure to have python installed and in PATH)"
pip3 install -r VRCNowPlaying/Requirements.txt
python3 VRCNowPlaying/vrcnowplaying.py
pause