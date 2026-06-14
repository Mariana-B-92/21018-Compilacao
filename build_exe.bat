@echo off
REM ===========================================================================
REM build_exe.bat - Gera o executavel standalone do compilador MOCP
REM
REM Pre-requisitos:
REM   - Python 3.10+ instalado e no PATH
REM   - Ficheiros gerados pelo ANTLR (MOCPLexer.py, MOCPParser.py,
REM     MOCPVisitor.py) presentes no diretorio actual
REM
REM Resultado: dist\mocp.exe
REM ===========================================================================

echo.
echo [1/4] A verificar dependencias...
where python >nul 2>&1
if errorlevel 1 (
    echo ERRO: Python nao encontrado no PATH.
    pause
    exit /b 1
)

if not exist "MOCPLexer.py" (
    echo ERRO: MOCPLexer.py nao encontrado.
    echo Execute primeiro: antlr4 -Dlanguage=Python3 -visitor MOCP.g4
    pause
    exit /b 1
)

echo.
echo [2/4] A instalar PyInstaller e antlr4-python3-runtime...
python -m pip install --upgrade pyinstaller antlr4-python3-runtime
if errorlevel 1 (
    echo ERRO: falha na instalacao das dependencias.
    pause
    exit /b 1
)

echo.
echo [3/4] A limpar builds anteriores...
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist
if exist "mocp.spec" del mocp.spec

echo.
echo [4/4] A construir o executavel (pode demorar 1-2 minutos)...
python -m PyInstaller ^
    --onefile ^
    --name mocp ^
    --console ^
    --hidden-import=antlr4 ^
    --collect-all antlr4 ^
    main.py

if errorlevel 1 (
    echo ERRO: falha na construcao do executavel.
    pause
    exit /b 1
)

echo.
echo ===========================================================================
echo Build concluido com sucesso!
echo Executavel: dist\mocp.exe
echo.
echo Para testar:
echo     dist\mocp.exe Testes\teste1.mocp
echo     dist\mocp.exe Testes\teste1.mocp -p3
echo ===========================================================================
echo.
pause