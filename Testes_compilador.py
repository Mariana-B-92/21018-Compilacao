import unittest
from antlr4 import InputStream, CommonTokenStream

from MOCPLexer import MOCPLexer
from MOCPParser import MOCPParser
from MOCPErrorListener import MOCPErrorListener
from MOCPSemanticAnalyzer import MOCPSemanticAnalyzer
from MOCPIntermediateCodeGenerator import MOCPIntermediateCodeGenerator
from MOCPCodeOptimiser import optimizar_completo


# =============================================================================
# Funções auxiliares partilhadas por todas as classes de testes
# =============================================================================

def _parse(codigo: str):
    """
    Faz o parse de um programa MOCP e devolve (tree, error_listener).
    """
    stream = InputStream(codigo)
    lexer = MOCPLexer(stream)
    tokens = CommonTokenStream(lexer)
    error_listener = MOCPErrorListener()
    lexer.removeErrorListeners()
    lexer.addErrorListener(error_listener)
    parser = MOCPParser(tokens)
    parser.removeErrorListeners()
    parser.addErrorListener(error_listener)
    tree = parser.program()
    return tree, error_listener


def _analisar_semanticamente(codigo: str):
    """
    Faz parse + análise semântica.
    Devolve (erros_lexico_sintatico, erros_semanticos, symbol_table).
    """
    tree, el = _parse(codigo)
    if el.errors:
        return el.errors, [], None
    analisador = MOCPSemanticAnalyzer()
    analisador.visit(tree)
    return [], analisador.errors, analisador.symbol_table


def _gerar_tac(codigo: str):
    """
    Faz parse + semântica + geração de TAC.
    Devolve lista de strings do TAC original (ou None se houver erros).
    """
    tree, el = _parse(codigo)
    if el.errors:
        return None, el.errors
    analisador = MOCPSemanticAnalyzer()
    analisador.visit(tree)
    if analisador.errors:
        return None, analisador.errors
    gerador = MOCPIntermediateCodeGenerator(analisador.symbol_table)
    gerador.visit(tree)
    return gerador.get_code_as_strings(), []


def _gerar_tac_otimizado(codigo: str):
    """
    Faz parse + semântica + geração de TAC + otimização.
    Devolve lista de strings do TAC otimizado (ou None se houver erros).
    """
    tree, el = _parse(codigo)
    if el.errors:
        return None, el.errors
    analisador = MOCPSemanticAnalyzer()
    analisador.visit(tree)
    if analisador.errors:
        return None, analisador.errors
    gerador = MOCPIntermediateCodeGenerator(analisador.symbol_table)
    gerador.visit(tree)
    quadruplos_otimizados = optimizar_completo(gerador.quadruplos)
    gerador_temp = MOCPIntermediateCodeGenerator(analisador.symbol_table)
    gerador_temp.quadruplos = quadruplos_otimizados
    return gerador_temp.get_code_as_strings(), []


# =============================================================================
# 1. Testes de Análise Semântica
# =============================================================================

class TestSemanticAnalyzer(unittest.TestCase):

    # ── Casos válidos ──────────────────────────────────────────────────────

    def test_programa_minimo_valido(self):
        """Programa com apenas a função principal é válido."""
        codigo = """
        vazio principal(vazio);
        vazio principal(vazio) {
            inteiro x;
            x = 5;
        }
        """
        _, erros_sem, _ = _analisar_semanticamente(codigo)
        self.assertEqual(erros_sem, [], f"Esperava sem erros, obteve: {erros_sem}")

    def test_funcao_com_parametros_e_chamada_valida(self):
        """Função com parâmetros e chamada com argumentos corretos."""
        codigo = """
        inteiro soma(inteiro, inteiro);
        vazio principal(vazio);
        inteiro soma(inteiro a, inteiro b) {
            retornar a + b;
        }
        vazio principal(vazio) {
            inteiro r;
            r = soma(1, 2);
        }
        """
        _, erros_sem, _ = _analisar_semanticamente(codigo)
        self.assertEqual(erros_sem, [], f"Esperava sem erros, obteve: {erros_sem}")

    def test_promocao_implicita_inteiro_para_real(self):
        """Atribuir inteiro a real é promoção implícita válida."""
        codigo = """
        vazio principal(vazio);
        vazio principal(vazio) {
            real x;
            x = 5;
        }
        """
        _, erros_sem, _ = _analisar_semanticamente(codigo)
        self.assertEqual(erros_sem, [], f"Esperava sem erros, obteve: {erros_sem}")

    def test_vetor_com_acesso_indexado_valido(self):
        """Acesso a vetor com índice inteiro é válido."""
        codigo = """
        vazio principal(vazio);
        vazio principal(vazio) {
            inteiro v[5];
            inteiro i;
            i = 0;
            v[i] = 10;
        }
        """
        _, erros_sem, _ = _analisar_semanticamente(codigo)
        self.assertEqual(erros_sem, [], f"Esperava sem erros, obteve: {erros_sem}")

    def test_cast_explicito_valido(self):
        """Cast explícito de real para inteiro é válido."""
        codigo = """
        vazio principal(vazio);
        vazio principal(vazio) {
            real x;
            inteiro k;
            x = 3.14;
            k = (inteiro) x;
        }
        """
        _, erros_sem, _ = _analisar_semanticamente(codigo)
        self.assertEqual(erros_sem, [], f"Esperava sem erros, obteve: {erros_sem}")

    def test_escopo_local_isolado(self):
        """Variável declarada numa função não é visível noutra."""
        codigo = """
        vazio func(vazio);
        vazio principal(vazio);
        vazio func(vazio) {
            inteiro x;
            x = 1;
        }
        vazio principal(vazio) {
            inteiro y;
            y = 2;
        }
        """
        _, erros_sem, _ = _analisar_semanticamente(codigo)
        self.assertEqual(erros_sem, [], f"Esperava sem erros, obteve: {erros_sem}")

    # ── Casos inválidos ────────────────────────────────────────────────────

    def test_erro_variavel_nao_declarada(self):
        """Usar variável não declarada deve gerar erro semântico."""
        codigo = """
        vazio principal(vazio);
        vazio principal(vazio) {
            x = 5;
        }
        """
        _, erros_sem, _ = _analisar_semanticamente(codigo)
        self.assertTrue(len(erros_sem) > 0, "Esperava erro semântico por variável não declarada")
        self.assertTrue(any("não foi declarada" in e or "não declarada" in e for e in erros_sem))

    def test_erro_variavel_declarada_duas_vezes(self):
        """Redeclarar variável no mesmo escopo deve gerar erro."""
        codigo = """
        vazio principal(vazio);
        vazio principal(vazio) {
            inteiro x;
            inteiro x;
        }
        """
        _, erros_sem, _ = _analisar_semanticamente(codigo)
        self.assertTrue(len(erros_sem) > 0, "Esperava erro por redeclaração")
        self.assertTrue(any("já foi declarada" in e or "já declarada" in e for e in erros_sem))

    def test_erro_atribuir_real_a_inteiro(self):
        """Atribuir real a inteiro sem cast deve gerar erro."""
        codigo = """
        vazio principal(vazio);
        vazio principal(vazio) {
            inteiro x;
            x = 3.14;
        }
        """
        _, erros_sem, _ = _analisar_semanticamente(codigo)
        self.assertTrue(len(erros_sem) > 0, "Esperava erro de tipo")

    def test_erro_funcao_nao_declarada(self):
        """Chamar função sem protótipo deve gerar erro."""
        codigo = """
        vazio principal(vazio);
        vazio principal(vazio) {
            inteiro r;
            r = funcaoInexistente(1);
        }
        """
        _, erros_sem, _ = _analisar_semanticamente(codigo)
        self.assertTrue(len(erros_sem) > 0, "Esperava erro por função não declarada")

    def test_erro_numero_errado_de_argumentos(self):
        """Chamar função com número errado de argumentos deve gerar erro."""
        codigo = """
        inteiro soma(inteiro, inteiro);
        vazio principal(vazio);
        inteiro soma(inteiro a, inteiro b) {
            retornar a + b;
        }
        vazio principal(vazio) {
            inteiro r;
            r = soma(1);
        }
        """
        _, erros_sem, _ = _analisar_semanticamente(codigo)
        self.assertTrue(len(erros_sem) > 0, "Esperava erro por número errado de argumentos")

    def test_erro_modulo_com_reais(self):
        """Operador % com reais deve gerar erro."""
        codigo = """
        vazio principal(vazio);
        vazio principal(vazio) {
            real x;
            real y;
            real z;
            x = 3.14;
            y = 2.0;
            z = x % y;
        }
        """
        _, erros_sem, _ = _analisar_semanticamente(codigo)
        self.assertTrue(len(erros_sem) > 0, "Esperava erro: % só para inteiros")

    def test_erro_escrever_com_string(self):
        """escrever() não aceita strings — deve gerar erro."""
        codigo = """
        vazio principal(vazio);
        vazio principal(vazio) {
            escrever("ola");
        }
        """
        _, erros_sem, _ = _analisar_semanticamente(codigo)
        self.assertTrue(len(erros_sem) > 0, "Esperava erro: escrever() não aceita strings")

    def test_erro_vetor_sem_indice_em_atribuicao(self):
        """Atribuir a vetor sem índice deve gerar erro."""
        codigo = """
        vazio principal(vazio);
        vazio principal(vazio) {
            inteiro v[5];
            v = 10;
        }
        """
        _, erros_sem, _ = _analisar_semanticamente(codigo)
        self.assertTrue(len(erros_sem) > 0, "Esperava erro: vetor sem índice")

    def test_erro_prototipo_em_falta(self):
        """Definir função sem protótipo deve gerar erro."""
        codigo = """
        vazio principal(vazio);
        inteiro soma(inteiro a, inteiro b) {
            retornar a + b;
        }
        vazio principal(vazio) {
            escrever(soma(1, 2));
        }
        """
        _, erros_sem, _ = _analisar_semanticamente(codigo)
        self.assertTrue(len(erros_sem) > 0, "Esperava erro: protótipo em falta")

    def test_erro_lers_para_vetor_real(self):
        """lers() só pode inicializar inteiro[] — não real[]."""
        codigo = """
        vazio principal(vazio);
        vazio principal(vazio) {
            real s[] = lers();
        }
        """
        _, erros_sem, _ = _analisar_semanticamente(codigo)
        self.assertTrue(len(erros_sem) > 0, "Esperava erro: lers() só para inteiro[]")

    def test_erro_funcao_void_retorna_valor(self):
        """Função vazio não pode retornar um valor."""
        codigo = """
        vazio func(vazio);
        vazio principal(vazio);
        vazio func(vazio) {
            retornar 1;
        }
        vazio principal(vazio) {
            func();
        }
        """
        _, erros_sem, _ = _analisar_semanticamente(codigo)
        self.assertTrue(len(erros_sem) > 0, "Esperava erro: vazio não pode retornar valor")


# =============================================================================
# 2. Testes de Geração de Código Intermédio (TAC)
# =============================================================================

class TestIntermediateCodeGenerator(unittest.TestCase):

    def test_tac_atribuicao_simples(self):
        """Atribuição simples gera instrução TAC de atribuição."""
        codigo = """
        vazio principal(vazio);
        vazio principal(vazio) {
            inteiro x;
            x = 42;
        }
        """
        tac, erros = _gerar_tac(codigo)
        self.assertIsNotNone(tac, f"Erros: {erros}")
        self.assertTrue(any("x = 42" in l for l in tac),
                        f"Esperava 'x = 42' no TAC. TAC: {tac}")

    def test_tac_funcao_com_parametros(self):
        """Função com parâmetros gera instruções de recepção paramN → nome."""
        codigo = """
        inteiro dobro(inteiro);
        vazio principal(vazio);
        inteiro dobro(inteiro n) {
            retornar n + n;
        }
        vazio principal(vazio) {
            escrever(dobro(5));
        }
        """
        tac, erros = _gerar_tac(codigo)
        self.assertIsNotNone(tac, f"Erros: {erros}")
        self.assertTrue(any("n = param1" in l for l in tac),
                        f"Esperava 'n = param1' no TAC. TAC: {tac}")

    def test_tac_ciclo_enquanto(self):
        """Ciclo enquanto gera label de início, ifFalse e goto."""
        codigo = """
        vazio principal(vazio);
        vazio principal(vazio) {
            inteiro x;
            x = 10;
            enquanto (x > 0) {
                x = x - 1;
            }
        }
        """
        tac, erros = _gerar_tac(codigo)
        self.assertIsNotNone(tac, f"Erros: {erros}")
        self.assertTrue(any("ifFalse" in l for l in tac),
                        f"Esperava 'ifFalse' no TAC. TAC: {tac}")
        self.assertTrue(any("goto" in l for l in tac),
                        f"Esperava 'goto' no TAC. TAC: {tac}")

    def test_tac_condicional_se_senao(self):
        """Condicional se/senao gera dois blocos com goto de separação."""
        codigo = """
        vazio principal(vazio);
        vazio principal(vazio) {
            inteiro x;
            x = 5;
            se (x > 3) {
                x = 1;
            } senao {
                x = 0;
            }
        }
        """
        tac, erros = _gerar_tac(codigo)
        self.assertIsNotNone(tac, f"Erros: {erros}")
        # Deve ter ifFalse (para o ramo senao) e goto (para saltar o senao)
        self.assertTrue(any("ifFalse" in l for l in tac))
        self.assertTrue(any("goto" in l for l in tac))

    def test_tac_acesso_a_vetor(self):
        """Acesso a vetor gera instruções de cálculo de offset e leitura."""
        codigo = """
        vazio principal(vazio);
        vazio principal(vazio) {
            inteiro v[3];
            inteiro x;
            inteiro i;
            i = 0;
            v[i] = 7;
            x = v[i];
        }
        """
        tac, erros = _gerar_tac(codigo)
        self.assertIsNotNone(tac, f"Erros: {erros}")
        # Deve haver acesso indexado v[...] e atribuição indexada v[...] =
        self.assertTrue(any("[" in l and "]" in l for l in tac),
                        f"Esperava acesso indexado no TAC. TAC: {tac}")

    def test_tac_chamada_de_funcao_builtin_ler(self):
        """ler() gera instrução call ler."""
        codigo = """
        vazio principal(vazio);
        vazio principal(vazio) {
            inteiro n;
            n = ler();
        }
        """
        tac, erros = _gerar_tac(codigo)
        self.assertIsNotNone(tac, f"Erros: {erros}")
        self.assertTrue(any("call ler" in l for l in tac),
                        f"Esperava 'call ler' no TAC. TAC: {tac}")

    def test_tac_escreverv(self):
        """escreverv() gera instrução writev com o nome do vetor."""
        codigo = """
        vazio principal(vazio);
        vazio principal(vazio) {
            inteiro v[3];
            escreverv(v);
        }
        """
        tac, erros = _gerar_tac(codigo)
        self.assertIsNotNone(tac, f"Erros: {erros}")
        self.assertTrue(any("writev v" in l for l in tac),
                        f"Esperava 'writev v' no TAC. TAC: {tac}")

    def test_tac_cast(self):
        """Cast explícito gera instrução cast no TAC."""
        codigo = """
        vazio principal(vazio);
        vazio principal(vazio) {
            real x;
            inteiro k;
            x = 3.14;
            k = (inteiro) x;
        }
        """
        tac, erros = _gerar_tac(codigo)
        self.assertIsNotNone(tac, f"Erros: {erros}")
        self.assertTrue(any("(inteiro)" in l for l in tac),
                        f"Esperava instrução de cast no TAC. TAC: {tac}")


# =============================================================================
# 3. Testes do Otimizador de Código Intermédio
# =============================================================================

class TestCodeOptimiser(unittest.TestCase):

    def test_constant_folding_soma(self):
        """Constant folding: 2 + 3 deve ser dobrado para 5."""
        codigo = """
        vazio principal(vazio);
        vazio principal(vazio) {
            inteiro x;
            x = 2 + 3;
            escrever(x);
        }
        """
        tac, erros = _gerar_tac_otimizado(codigo)
        self.assertIsNotNone(tac, f"Erros: {erros}")
        # Não deve existir "2 + 3" após folding
        self.assertFalse(any("2 + 3" in l for l in tac),
                         f"'2 + 3' não devia existir após folding. TAC: {tac}")

    def test_constant_folding_cadeia(self):
        """Constant folding em cadeia: (5 + 10) * 2 deve resultar em 30."""
        codigo = """
        vazio principal(vazio);
        vazio principal(vazio) {
            inteiro a;
            inteiro b;
            inteiro c;
            inteiro d;
            a = 5;
            b = 10;
            c = a + b;
            d = c * 2;
            escrever(d);
        }
        """
        tac, erros = _gerar_tac_otimizado(codigo)
        self.assertIsNotNone(tac, f"Erros: {erros}")
        self.assertTrue(any("write 30" in l or "write" in l and "30" in l for l in tac),
                        f"Esperava 'write 30' após folding. TAC: {tac}")

    def test_eliminacao_codigo_morto(self):
        """Variável calculada mas nunca usada deve ser eliminada."""
        codigo = """
        vazio principal(vazio);
        vazio principal(vazio) {
            inteiro x;
            inteiro y;
            x = 10;
            y = x + 5;
        }
        """
        tac, erros = _gerar_tac_otimizado(codigo)
        self.assertIsNotNone(tac, f"Erros: {erros}")
        # y e o cálculo y = x + 5 devem ser eliminados (y nunca é usado)
        self.assertFalse(any("y =" in l for l in tac),
                         f"'y =' devia ter sido eliminado. TAC: {tac}")

    def test_propagacao_copias(self):
        """Propagação de cópias: x = y; z = x → z = y."""
        codigo = """
        vazio principal(vazio);
        vazio principal(vazio) {
            inteiro a;
            inteiro b;
            inteiro c;
            a = 100;
            escrever(a);
            b = a;
            a = 10;
            c = b + 20;
            escrever(c);
        }
        """
        tac, erros = _gerar_tac_otimizado(codigo)
        self.assertIsNotNone(tac, f"Erros: {erros}")
        # O resultado final write deve ser 120 (b=100, c=100+20)
        self.assertTrue(any("120" in l for l in tac),
                        f"Esperava '120' após propagação de cópias. TAC: {tac}")

    def test_eliminacao_codigo_inatingivel(self):
        """Código após return numa função deve ser eliminado."""
        codigo = """
        inteiro obter(vazio);
        vazio principal(vazio);
        inteiro obter(vazio) {
            retornar 42;
            inteiro x;
            x = 99;
        }
        vazio principal(vazio) {
            inteiro r;
            r = obter();
            escrever(r);
        }
        """
        tac, erros = _gerar_tac_otimizado(codigo)
        self.assertIsNotNone(tac, f"Erros: {erros}")
        # x = 99 é código inatingível e deve ter sido eliminado
        self.assertFalse(any("x = 99" in l for l in tac),
                         f"'x = 99' devia ter sido eliminado como código inatingível. TAC: {tac}")

    def test_tac_valido_apos_otimizacao(self):
        """O TAC otimizado deve sempre conter o label principal e halt."""
        codigo = """
        vazio principal(vazio);
        vazio principal(vazio) {
            inteiro x;
            x = 1;
            escrever(x);
        }
        """
        tac, erros = _gerar_tac_otimizado(codigo)
        self.assertIsNotNone(tac, f"Erros: {erros}")
        self.assertTrue(any("principal:" in l for l in tac),
                        f"TAC otimizado deve ter label 'principal:'. TAC: {tac}")
        self.assertTrue(any("halt" in l for l in tac),
                        f"TAC otimizado deve ter 'halt'. TAC: {tac}")

    def test_cse_subexpressao_comum(self):
        """CSE: a mesma expressão calculada duas vezes deve ser reutilizada."""
        codigo = """
        vazio principal(vazio);
        vazio principal(vazio) {
            inteiro a;
            inteiro b;
            inteiro x;
            inteiro y;
            a = 3;
            b = 4;
            x = a + b;
            y = a + b;
            escrever(x);
            escrever(y);
        }
        """
        tac, erros = _gerar_tac_otimizado(codigo)
        self.assertIsNotNone(tac, f"Erros: {erros}")
        # Após CSE e folding, a + b = 7 deve aparecer no máximo uma vez como operação
        ops_soma = [l for l in tac if "+" in l and "3" in l and "4" in l]
        self.assertLessEqual(len(ops_soma), 1,
                             f"CSE devia eliminar operação duplicada. TAC: {tac}")

# =============================================================================
# 4. Testes de Geração de Código Final P3 Assembly
# =============================================================================

from MOCPCodeGenerator_P3 import code_generator_p3


def _gerar_p3(codigo: str):
    """
    Faz parse + semântica + geração de TAC + otimização + geração P3.
    Devolve (codigo_assembly, has_real_type, erros).
    """
    tree, el = _parse(codigo)
    if el.errors:
        return None, False, el.errors
    analisador = MOCPSemanticAnalyzer()
    analisador.visit(tree)
    if analisador.errors:
        return None, analisador.has_real_type, analisador.errors
    if analisador.has_real_type:
        return None, True, []
    gerador = MOCPIntermediateCodeGenerator(analisador.symbol_table)
    gerador.visit(tree)
    quadruplos_otimizados = optimizar_completo(gerador.quadruplos)
    codigo_as = code_generator_p3(quadruplos_otimizados)
    return codigo_as, False, []


class TestCodeGeneratorP3(unittest.TestCase):

    def test_recusa_real_em_declaracao(self):
        """Declarar uma variável como real deve activar has_real_type."""
        codigo = """
        vazio principal(vazio);
        vazio principal(vazio) {
            real x = 3.14;
            inteiro k = (inteiro) x;
            escrever(k);
        }
        """
        _, has_real, erros = _gerar_p3(codigo)
        self.assertEqual(erros, [], f"Esperava sem erros, obteve: {erros}")
        self.assertTrue(has_real, "Variável real devia activar has_real_type")

    def test_recusa_real_em_retorno_de_funcao(self):
        """Função com tipo de retorno real deve activar has_real_type."""
        codigo = """
        real raiz();
        vazio principal(vazio);
        real raiz() {
            retornar 1.5;
        }
        vazio principal(vazio) {
            real r = raiz();
            inteiro k = (inteiro) r;
            escrever(k);
        }
        """
        _, has_real, erros = _gerar_p3(codigo)
        self.assertEqual(erros, [], f"Esperava sem erros, obteve: {erros}")
        self.assertTrue(has_real, "Retorno real devia activar has_real_type")

    def test_recusa_real_em_cast(self):
        """Cast (real) deve activar has_real_type."""
        codigo = """
        vazio principal(vazio);
        vazio principal(vazio) {
            inteiro a = 5;
            real r = (real) a;
            inteiro k = (inteiro) r;
            escrever(k);
        }
        """
        _, has_real, erros = _gerar_p3(codigo)
        self.assertEqual(erros, [], f"Esperava sem erros, obteve: {erros}")
        self.assertTrue(has_real, "Cast (real) devia activar has_real_type")

    def test_aceita_programa_so_inteiros(self):
        """Programa só com inteiros não activa has_real_type e gera assembly."""
        codigo = """
        vazio principal(vazio);
        vazio principal(vazio) {
            inteiro x = 5;
            inteiro y = 10;
            escrever(x + y);
        }
        """
        code, has_real, erros = _gerar_p3(codigo)
        self.assertEqual(erros, [], f"Esperava sem erros, obteve: {erros}")
        self.assertFalse(has_real, "Programa só com inteiros não devia activar has_real_type")
        self.assertIsNotNone(code, "Esperava código P3 gerado")

    def test_estrutura_basica_do_assembly(self):
        """O assembly contém as secções obrigatórias do template P3."""
        codigo = """
        vazio principal(vazio);
        vazio principal(vazio) {
            escrever(42);
        }
        """
        code, _, erros = _gerar_p3(codigo)
        self.assertIsNotNone(code, f"Erros: {erros}")
        self.assertIn("ORIG     0000h", code, "Falta 'ORIG 0000h' (zona de código)")
        self.assertIn("ORIG     8000h", code, "Falta 'ORIG 8000h' (zona de dados)")
        self.assertIn("CALL     principal", code, "Falta CALL inicial à principal")
        self.assertIn("FIM:", code, "Falta label FIM (loop de halt)")

    def test_prologo_e_epilogo_das_funcoes(self):
        """Funções têm prólogo PUSH R5; MOV R5, SP e epílogo MOV SP, R5; POP R5; RET."""
        codigo = """
        inteiro fact(inteiro);
        vazio principal(vazio);
        inteiro fact(inteiro k) {
            se (k <= 1) {
                retornar 1;
            } senao {
                retornar k * fact(k - 1);
            }
        }
        vazio principal(vazio) {
            escrever(fact(5));
        }
        """
        code, _, erros = _gerar_p3(codigo)
        self.assertIsNotNone(code, f"Erros: {erros}")
        self.assertIn("PUSH     R5", code, "Falta 'PUSH R5' no prólogo")
        self.assertIn("MOV      R5, SP", code, "Falta 'MOV R5, SP' no prólogo")
        self.assertIn("MOV      SP, R5", code, "Falta 'MOV SP, R5' no epílogo")
        self.assertIn("POP      R5", code, "Falta 'POP R5' no epílogo")
        self.assertIn("RET", code, "Falta 'RET' no epílogo")

    def test_parametros_acedidos_via_FP_mais_3(self):
        """param1 deve ser acedido via M[R5+3] (FP+3), não FP+2."""
        codigo = """
        inteiro fact(inteiro);
        vazio principal(vazio);
        inteiro fact(inteiro k) {
            se (k <= 1) {
                retornar 1;
            } senao {
                retornar k * fact(k - 1);
            }
        }
        vazio principal(vazio) {
            escrever(fact(5));
        }
        """
        code, _, erros = _gerar_p3(codigo)
        self.assertIsNotNone(code, f"Erros: {erros}")
        self.assertIn("M[R5+3]", code, "param1 devia ser acedido via M[R5+3]")
        self.assertNotIn("M[R5+2]", code, "M[R5+2] é o endereço de retorno, não pode ser usado para parâmetros")

    def test_mul_recupera_LSW(self):
        """Após 'MUL R1, R2' deve haver 'MOV R1, R2' para recuperar o LSW."""
        codigo = """
        inteiro multiplica(inteiro, inteiro);
        vazio principal(vazio);
        inteiro multiplica(inteiro a, inteiro b) {
            retornar a * b;
        }
        vazio principal(vazio) {
            escrever(multiplica(3, 4));
        }
        """
        code, _, erros = _gerar_p3(codigo)
        self.assertIsNotNone(code, f"Erros: {erros}")
        lines = code.split('\n')
        encontrou_mul = False
        for i, line in enumerate(lines):
            if "MUL" in line and "R1, R2" in line:
                janela = " ".join(lines[i + 1:i + 3])
                self.assertIn("MOV", janela, "Falta MOV após MUL para recuperar o LSW")
                self.assertIn("R1, R2", janela, "MOV deveria copiar R2 (LSW) para R1")
                encontrou_mul = True
                break
        self.assertTrue(encontrou_mul, "Esperava 'MUL R1, R2' no código gerado")

    def test_helpers_io_sao_sempre_emitidos(self):
        """As subrotinas auxiliares de I/O são incluídas no output."""
        codigo = """
        vazio principal(vazio);
        vazio principal(vazio) {
            escrever(1);
        }
        """
        code, _, erros = _gerar_p3(codigo)
        self.assertIsNotNone(code, f"Erros: {erros}")
        self.assertIn("WRITE:", code, "Falta subrotina WRITE")
        self.assertIn("WRITES:", code, "Falta subrotina WRITES")
        self.assertIn("READ:", code, "Falta subrotina READ")
        self.assertIn("WRITEV:", code, "Falta subrotina WRITEV")
        
# =============================================================================
# Ponto de entrada
# =============================================================================

if __name__ == "__main__":
    unittest.main(verbosity=2)