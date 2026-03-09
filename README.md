*MOCP - My Own Compiler Project


UAb 2024/2025 – Unidade Curricular de Compilação

Este projeto tem como objetivo o desenvolvimento de um compilador para a linguagem MOCP (My Own Compiler Project), uma linguagem fictícia inspirada em C, cuja gramática foi simplificada e adaptada para fins didáticos e de análise de compiladores.

*Introdução
A linguagem MOC foi concebida com o propósito de facilitar o estudo e a experimentação dos conceitos de análise léxica e sintática, recorrendo a ferramentas como o ANTLR4. Este repositório disponibiliza a gramática completa desenvolvida em ANTLR, bem como os scripts necessários para a compilação, análise e validação de programas escritos nesta linguagem.

|Requisitos recomendados:

||Python 3.10 ou superior
||ANTLR versão 4.13.2
||Sistema com Java instalado (necessário para o ANTLR)

*Estrutura do Projeto

*Como executar
Instalar o Python
Este projeto requer Python 3.10 ou superior.

Windows
Vá a https://www.python.org/downloads/windows/
Clique em “Download Python 3.X”
Durante a instalação, ative a opção Add Python to PATH
Verificar a instalação:
python --version

*Terminal recomendado: Git Bash
Para que o comando main.py -tree funcione corretamente no Windows, é necessário usar um terminal compatível com comandos Unix, como cat. O terminal Git Bash é a forma mais simples de garantir essa compatibilidade.

Como instalar o Git Bash:
Vá a: https://git-scm.com/download/win
Faça o download do executável para Windows mais recente
Durante a instalação, pode aceitar todas as opções por defeito
Após a instalação, abra o Git Bash (procure "Git Bash" no menu Iniciar, ou altere o tipo de terminal no IDE que está a usar)
Como utilizar:
No Git Bash, pode executar os comandos do projeto normalmente. Exemplo:

python3 main.py Exemplos_Teste/teste1.txt -tree

*Preparar ambiente
Instale o ANTLR4 e adicione ao PATH (ver instruções em: https://github.com/antlr/antlr4)
Instale dependências:
pip install antlr4-python3-runtime

*Compilar
antlr4 -Dlanguage=Python3 -visitor MOC.g4
