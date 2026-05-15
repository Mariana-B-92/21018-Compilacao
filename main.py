import sys

from antlr4 import *

from MOCPLexer import MOCPLexer
from MOCPParser import MOCPParser
from MOCPErrorListener import MOCPErrorListener
from MOCPSemanticAnalyzer import MOCPSemanticAnalyzer
from MOCPIntermediateCodeGenerator import MOCPIntermediateCodeGenerator
from MOCPCodeOptimiser import optimizar_completo
from utils import run_antlr4_parse


def main():
    if len(sys.argv) < 2:
        print("Uso: python3 main.py <ficheiro.txt> [-tree | -gui]")
        return

    input_file = sys.argv[1]

    # Suporte a opções -tree e -gui (delegam no antlr4-parse)
    if "-tree" in sys.argv:
        run_antlr4_parse(input_file, "-tree")
        return
    if "-gui" in sys.argv:
        run_antlr4_parse(input_file, "-gui")
        return

    # ------------------------------------------------------------------
    # Leitura do ficheiro de entrada
    # ------------------------------------------------------------------
    try:
        input_stream = FileStream(input_file, encoding="utf-8")
    except FileNotFoundError:
        print(f"Erro: ficheiro '{input_file}' não encontrado.")
        return

    # ------------------------------------------------------------------
    # Análise Léxica e Sintática
    # ------------------------------------------------------------------
    print("--- A iniciar Análise Sintática ---")

    lexer = MOCPLexer(input_stream)
    tokens_stream = CommonTokenStream(lexer)

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

    if error_listener.errors:
        print("\nErros encontrados:")
        for error in error_listener.errors:
            print(error)
        return

    print("--- Análise Sintática concluída ---")

    # ------------------------------------------------------------------
    # Análise Semântica
    # ------------------------------------------------------------------
    print("--- A iniciar Análise Semântica ---")

    semantic_analyzer = MOCPSemanticAnalyzer()
    semantic_analyzer.visit(tree)

    if semantic_analyzer.errors:
        print("\nErros semânticos:")
        for error in semantic_analyzer.errors:
            print(error)
        print("\nErros semânticos encontrados. A abortar o processo de geração de código intermédio.")
        return

    print("--- Análise Semântica concluída ---")

    # ------------------------------------------------------------------
    # Geração de Código Intermédio (TAC em quádruplas estruturadas)
    # ------------------------------------------------------------------
    print("--- A iniciar Geração de Código Intermédio ---")

    generator = MOCPIntermediateCodeGenerator(semantic_analyzer.symbol_table)
    generator.visit(tree)

    print("--- Geração de Código Intermédio concluída ---")

    print("\n==== CÓDIGO TAC GERADO ====")
    for line in generator.get_code_as_strings():
        print(line)

    # ------------------------------------------------------------------
    # Otimização do Código Intermédio
    # ------------------------------------------------------------------
    quadruplos_otimizados = optimizar_completo(
        generator.quadruplos,
        variaveis_utilizador=set()
    )

    generator_temp = MOCPIntermediateCodeGenerator(semantic_analyzer.symbol_table)
    generator_temp.quadruplos = quadruplos_otimizados

    print("\n==== CÓDIGO TAC OTIMIZADO ====")
    for line in generator_temp.get_code_as_strings():
        print(line)


if __name__ == "__main__":
    main()
