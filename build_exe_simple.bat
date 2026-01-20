@echo off
echo =============================================
echo   GST Billing - EXE Builder
echo =============================================
echo.

REM Install dependencies
echo [1/4] Installing dependencies...
pip install customtkinter pillow reportlab num2words python-dateutil pyinstaller

echo.
echo [2/4] Creating application icon...
python assets\create_icon.py

echo.
echo [3/4] Building executable (this takes 2-5 minutes)...
echo.

REM Check if icon was created
if exist "assets\icon.ico" (
    echo Using custom icon...
    pyinstaller --onefile --windowed ^
        --name "GST_Billing" ^
        --icon "assets\icon.ico" ^
        --hidden-import customtkinter ^
        --hidden-import PIL._tkinter_finder ^
        --hidden-import reportlab.graphics ^
        --hidden-import num2words ^
        --hidden-import dateutil ^
        --collect-all customtkinter ^
        main.py
) else (
    echo Building without icon...
    pyinstaller --onefile --windowed ^
        --name "GST_Billing" ^
        --hidden-import customtkinter ^
        --hidden-import PIL._tkinter_finder ^
        --hidden-import reportlab.graphics ^
        --hidden-import num2words ^
        --hidden-import dateutil ^
        --collect-all customtkinter ^
        main.py
)

echo.
echo [4/4] Finalizing...

if exist "dist\GST_Billing.exe" (
    echo.
    echo =============================================
    echo   SUCCESS! Build Complete!
    echo =============================================
    echo.
    echo   Your EXE file is ready at:
    echo   dist\GST_Billing.exe
    echo.
    echo   File size:
    for %%A in (dist\GST_Billing.exe) do echo   %%~zA bytes
    echo.
    echo   You can now copy this file to your shop PC!
    echo =============================================
) else (
    echo.
    echo Build may have encountered issues.
    echo Check the output above for errors.
)

echo.
pause
