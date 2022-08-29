@echo off
echo "Installing requirements (be sure to have python installed and in PATH)"
pip install -r VRCNowPlaying/Requirements_nocutlet.txt
python VRCNowPlaying/vrcnowplaying.py
pause