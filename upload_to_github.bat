@echo off
echo =============================================
echo   Upload GST Billing to GitHub
echo =============================================
echo.

REM Check if git is installed
git --version >nul 2>&1
if errorlevel 1 (
    echo Git is not installed!
    echo.
    echo Please download and install Git from:
    echo https://git-scm.com/download/win
    echo.
    echo After installing, run this script again.
    pause
    exit /b 1
)

echo Git is installed. Proceeding...
echo.

set /p GITHUB_USERNAME=Enter your GitHub username:
set /p REPO_NAME=Enter repository name (default: gst-billing):

if "%REPO_NAME%"=="" set REPO_NAME=gst-billing

echo.
echo Setting up repository...

git init
git add .
git commit -m "Initial commit: GST Billing Software"
git branch -M main
git remote add origin https://github.com/%GITHUB_USERNAME%/%REPO_NAME%.git

echo.
echo Pushing to GitHub...
echo You may be asked to login to GitHub in a browser window.
echo.

git push -u origin main

echo.
echo =============================================
echo   Done!
echo =============================================
echo.
echo Your code is now on GitHub at:
echo https://github.com/%GITHUB_USERNAME%/%REPO_NAME%
echo.
echo GitHub Actions will now automatically build the EXE.
echo Go to: https://github.com/%GITHUB_USERNAME%/%REPO_NAME%/actions
echo.
echo Wait 3-5 minutes, then download your EXE from:
echo https://github.com/%GITHUB_USERNAME%/%REPO_NAME%/releases
echo.
pause
