@echo off
echo =============================================
echo   GST Billing Software - Build EXE
echo =============================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found!
    echo Please install Python 3.8 or higher from https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/5] Installing required packages...
pip install customtkinter pillow reportlab num2words python-dateutil pyinstaller matplotlib openpyxl

echo.
echo [2/5] Creating application icon...
python assets\create_icon.py

echo.
echo [3/5] Cleaning previous builds...
if exist "dist" rmdir /s /q dist
if exist "build\GST_Billing" rmdir /s /q "build\GST_Billing"

echo.
echo [4/5] Building executable...
echo This may take a few minutes...
echo.

pyinstaller --clean --noconfirm build/build.spec

if errorlevel 1 (
    echo.
    echo ERROR: Build failed!
    echo.
    echo Trying alternative build method...
    echo.

    if exist "assets\icon.ico" (
        pyinstaller --onefile --windowed --name "GST_Billing" ^
            --icon "assets\icon.ico" ^
            --add-data "assets;assets" ^
            --hidden-import customtkinter ^
            --hidden-import PIL ^
            --hidden-import reportlab ^
            --hidden-import num2words ^
            --hidden-import dateutil ^
            --hidden-import matplotlib ^
            --hidden-import matplotlib.backends.backend_tkagg ^
            --hidden-import openpyxl ^
            --collect-all matplotlib ^
            main.py
    ) else (
        pyinstaller --onefile --windowed --name "GST_Billing" ^
            --add-data "assets;assets" ^
            --hidden-import customtkinter ^
            --hidden-import PIL ^
            --hidden-import reportlab ^
            --hidden-import num2words ^
            --hidden-import dateutil ^
            --hidden-import matplotlib ^
            --hidden-import matplotlib.backends.backend_tkagg ^
            --hidden-import openpyxl ^
            --collect-all matplotlib ^
            main.py
    )
)

echo.
echo [5/5] Build complete!
echo.

if exist "dist\GST_Billing.exe" (
    echo =============================================
    echo   SUCCESS! Executable created at:
    echo   dist\GST_Billing.exe
    echo =============================================
    echo.
    echo You can now copy GST_Billing.exe to any Windows PC
    echo and run it without installing Python!
    echo.

    REM Create a shortcut-friendly folder
    if not exist "dist\GST_Billing_Portable" mkdir "dist\GST_Billing_Portable"
    copy "dist\GST_Billing.exe" "dist\GST_Billing_Portable\"

    echo A portable folder has been created at:
    echo   dist\GST_Billing_Portable\
    echo.
) else (
    echo.
    echo WARNING: Could not find the executable.
    echo Check the dist folder for output files.
)

pause
