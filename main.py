import os
import sys

from antlr4 import *

from MOCPLexer import MOCPLexer
from MOCPParser import MOCPParser
from MOCPErrorListener import MOCPErrorListener
from MOCPSemanticAnalyzer import MOCPSemanticAnalyzer
from MOCPIntermediateCodeGenerator import MOCPIntermediateCodeGenerator
from MOCPCodeOptimiser import optimizar_completo
from MOCPCodeGenerator_P3 import code_generator_p3
from utils import run_antlr4_parse


def main():
    if len(sys.argv) < 2:
        print("Uso: python3 main.py <ficheiro.mocp> [-tree | -gui | -p3]")
        print("  -tree : Árvore textual (via antlr4-parse)")
        print("  -gui  : GUI da árvore (via antlr4-parse)")
        print("  -p3   : Gera código P3 Assembly em Output_P3/<ficheiro>.as")
        return

    input_file = sys.argv[1]
    gen_p3 = "-p3" in sys.argv

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

    # ------------------------------------------------------------------
    # Geração de Código Final P3 Assembly (opcional via -p3)
    # ------------------------------------------------------------------
    if gen_p3:
        print("\n--- A iniciar Geração de Código P3 Assembly ---")

        # Verificação prévia: o P3 não tem unidade de vírgula flutuante.
        # Se o programa usa o tipo 'real' em qualquer ponto (declarações,
        # parâmetros, retornos ou casts), abortar antes de tentar gerar.
        if semantic_analyzer.has_real_type:
            print(
                "[Erro Geração P3] Tipo 'real' não é suportado pelo CPU P3 "
                "(sem unidade de vírgula flutuante)."
            )
            print("Geração de código P3 abortada.")
            return

        try:
            # Nome do ficheiro .as derivado do nome do ficheiro de entrada
            base = os.path.splitext(os.path.basename(input_file))[0]
            output_dir = os.path.join(os.path.dirname(os.path.abspath(input_file)) or ".", "..", "Output_P3")
            output_dir = os.path.normpath(output_dir)
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, f"{base}.as")

            code = code_generator_p3(quadruplos_otimizados)
            with open(output_path, "w", encoding="ascii", errors="replace") as f:
                f.write(code)

            print(f"--- Geração de Código P3 Assembly concluída ---")
            print(f"Ficheiro gravado em: {output_path}")
            print("Simulador: https://p3js.goncalomb.com/")
        except ValueError as e:
            # Erro de geração P3 (fallback do _check_no_real para literais reais)
            print(f"\n{e}")
            print("Geração de código P3 abortada.")


if __name__ == "__main__":
    main()