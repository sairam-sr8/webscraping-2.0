@echo off
REM Batch file to upload the current folder to a new GitHub repository
REM Usage: Double-click this file in your project folder

REM Set your GitHub username and email
set GITHUB_USERNAME=sairam-sr8
set GITHUB_EMAIL=sairam.sr08@gmail.com

REM Prompt for repository name
set /p REPO_NAME="Enter the name for your GitHub repository: "

REM Initialize git if not already a repo
if not exist .git (
    git init
    git config user.name "%GITHUB_USERNAME%"
    git config user.email "%GITHUB_EMAIL%"
)

REM Add all files
git add .

REM Commit changes
set /p COMMIT_MSG="Enter commit message: "
git commit -m "%COMMIT_MSG%"

REM Create GitHub repo using gh CLI (requires GitHub CLI installed and authenticated)
gh repo create %REPO_NAME% --public --source=. --remote=origin --push

REM If repo already exists, just push
if %errorlevel% neq 0 (
    git remote add origin https://github.com/%GITHUB_USERNAME%/%REPO_NAME%.git 2>nul
    git branch -M main
    git push -u origin main
)

pause
