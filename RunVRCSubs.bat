@echo off
echo "Installing requirements (be sure to have python installed and in PATH)"
pip install -r VRCSubs/Requirements.txt
python VRCSubs/vrcsubs.py
pause