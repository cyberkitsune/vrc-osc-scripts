@echo off
python --help >nul 2>&1
Setlocal EnableDelayedExpansion
IF !ERRORLEVEL! NEQ 0 (
    WHERE winget
    IF !ERRORLEVEL! NEQ 0 (
        echo "It appears you do not have Python installed! Please install Python 3.9 or higher from python.org or the Microsoft Store."
        pause
        exit
    ) ELSE (
        choice /C:yn /m "You do not have Python installed. Do you wish to install it? [Y] / [N]"
        if !ERRORLEVEL! == 1 (
            winget install python
        )
    )
) ELSE (
    echo "Python is installed!"
)