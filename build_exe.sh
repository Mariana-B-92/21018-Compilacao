#!/bin/bash
# =============================================================================
# build_exe.sh - Gera o executável standalone do compilador MOCP (Linux/Mac)
#
# Pré-requisitos:
#   - Python 3.10+ instalado
#   - Ficheiros gerados pelo ANTLR (MOCPLexer.py, MOCPParser.py,
#     MOCPVisitor.py) presentes no diretório actual
#
# Resultado: dist/mocp
# =============================================================================

set -e

echo
echo "[1/4] A verificar dependências..."
if ! command -v python3 >/dev/null 2>&1; then
    echo "ERRO: python3 não encontrado no PATH."
    exit 1
fi

if [ ! -f "MOCPLexer.py" ]; then
    echo "ERRO: MOCPLexer.py não encontrado."
    echo "Execute primeiro: antlr4 -Dlanguage=Python3 -visitor MOCP.g4"
    exit 1
fi

echo
echo "[2/4] A instalar PyInstaller e antlr4-python3-runtime..."
python3 -m pip install --upgrade pyinstaller antlr4-python3-runtime

echo
echo "[3/4] A limpar builds anteriores..."
rm -rf build dist mocp.spec

echo
echo "[4/4] A construir o executável (pode demorar 1-2 minutos)..."
python3 -m PyInstaller \
    --onefile \
    --name mocp \
    --console \
    --hidden-import=antlr4 \
    --collect-all antlr4 \
    main.py

echo
echo "============================================================================="
echo "Build concluído com sucesso!"
echo "Executável: dist/mocp"
echo
echo "Para testar:"
echo "    ./dist/mocp Testes/teste1.mocp"
echo "    ./dist/mocp Testes/teste1.mocp -p3"
echo "============================================================================="