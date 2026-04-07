import sys
import subprocess
from antlr4 import *
from MOCPLexer import MOCPLexer
from MOCPParser import MOCPParser
from MOCPErrorListener import MOCPErrorListener
from MOCPSemanticAnalyzer import MOCPSemanticAnalyzer

def run_antlr4_parse(file_path, option):
    cmd = f"cat {file_path} | antlr4-parse MOCP.g4 program {option}"
    subprocess.run(cmd, shell=True)

def main():
    if len(sys.argv) < 2:
        print("Uso: python3 main.py <Testes/ficheiro.txt> [-tree | -gui]")
        return

    input_file = sys.argv[1]

    if "-tree" in sys.argv:
        run_antlr4_parse(input_file, "-tree")
        return

    if "-gui" in sys.argv:
        run_antlr4_parse(input_file, "-gui")
        return

    input_stream = FileStream(input_file, encoding='utf-8')

    # Análise Sintática/Léxica:
    lexer = MOCPLexer(input_stream)
    tokens_stream = CommonTokenStream(lexer)

    # Tratamento de Erros:
    error_listener = MOCPErrorListener()
    lexer.removeErrorListeners()
    lexer.addErrorListener(error_listener)

    parser = MOCPParser(tokens_stream)
    parser.removeErrorListeners()
    parser.addErrorListener(error_listener)

    try:
        tree = parser.program()
    except Exception as e:
        print(f"\n[Parsing interrompido]: {e}")
        return

    # Se houver erros sintáticos/léxicos:
    if error_listener.errors:
        print("\nErros encontrados:")
        for error in error_listener.errors:
            print(error)
        return

    # Análise semântica
    semantic_analyzer = MOCPSemanticAnalyzer()
    semantic_analyzer.visit(tree)

    if semantic_analyzer.errors:
        print("\nErros semânticos:")
        for error in semantic_analyzer.errors:
            print(error)
    else:
       print("Programa semanticamente correto.")


if __name__ == '__main__':
    main()
