@echo off
Setlocal EnableDelayedExpansion
python --help >nul 2>&1
IF !ERRORLEVEL! NEQ 0 (
    WHERE winget
    IF !ERRORLEVEL! NEQ 0 (
        echo "It appears you do not have Python installed! Please install Python 3.9 or higher from python.org or the Microsoft Store."
        pause
        exit
    ) ELSE (
        choice /C:yn /m "You do not have Python installed. Do you wish to install it? [Y] / [N]"
        if !ERRORLEVEL! == 1 (
            echo "Please accept any licence agreements after this to install python by pressing Y then enter."
            winget install python
            if !ERRORLEVEL! NEQ 0 (
                echo "For some reason Python failed to install with winget, install Python manually with the windows store or using python.org"
                echo "Feel free to contact the vrc-osc-scripts Discord for more help"
                pause
                exit
            )
        )
    )
) ELSE (
    echo "Python is installed!"
)