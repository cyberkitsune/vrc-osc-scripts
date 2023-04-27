@echo off
echo [%~n0] Checking for updates...
python -m pip install -r Requirements.txt -q
python Updatecheck.py