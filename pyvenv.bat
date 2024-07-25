@echo off
echo Setting up virtual environment
pip show virtualenv >nul 2>&1
if %errorlevel% neq 0 (
    @echo - Installing virtualenv
    pip install virtualenv
) else (
    @echo - virtualenv already installed
)
if not exist venv (
    @echo - Creating new virtual environment
    call virtualenv venv
) else (
    @echo - Using existing virtual environment (venv)
)
pushd venv\Scripts
if "%1" == "0" (
    echo - Deactivating virtual environment
    call deactivate
) else (
    echo - Activating virtual environment
    call activate
)
popd
