import sys
import subprocess
from antlr4 import *
from MOCPLexer import MOCPLexer
from MOCPParser import MOCPParser
from MOCPErrorListener import MOCPErrorListener
# from SemanticAnalyzer import SemanticAnalyzer


def run_antlr4_parse(file_path, option):
    cmd = f"cat {file_path} | antlr4-parse MOCP.g4 programa {option}"
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
    lexer = MOCPLexer(input_stream)
    token_stream = CommonTokenStream(lexer)

    listener = MOCPErrorListener()

    lexer.removeErrorListeners()
    lexer.addErrorListener(listener)

    parser = MOCPParser(token_stream)
    parser.removeErrorListeners()
    parser.addErrorListener(listener)

    try:
        tree = parser.programa()
    except Exception as e:
        print(f"\n[Parsing interrompido]: {e}")
        return

    # Se houver erros sintáticos/léxicos
    if listener.erros:
        print("\nErros encontrados:")
        for erro in listener.erros:
            print(erro)
        return

    # Análise semântica
    # semantic = SemanticAnalyzer()
    # semantic.visit(tree)

    #if semantic.erros:
    #    print("\nErros semânticos:")
    #   for erro in semantic.erros:
    #        print(f"[Erro Semântico] {erro}")
    #else:
    #    print("Programa semanticamente correto.")


if __name__ == '__main__':
    main()
