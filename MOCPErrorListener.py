from antlr4.error.ErrorListener import ErrorListener
import re

class MOCPErrorListener(ErrorListener):
    # Listener responsável por capturar e adaptar erros do ANTLR para a linguagem MOCP.
    # Traduz mensagens de erro léxico e sintático em sugestões amigáveis.

    # Palavras-chave da linguagem C que não são suportadas em MOCP
    PALAVRAS_C_PROIBIDAS = {
        'int', 'double', 'void', 'main', 'if', 'else', 'while', 'for', 'return',
        'char', 'short', 'long', 'float', 'unsigned', 'signed',
        'struct', 'union', 'enum', 'typedef',
        'switch', 'case', 'default', 'break', 'continue', 'goto',
        'static', 'extern', 'register', 'auto', 'const', 'volatile'
    }

    # Operadores do C que não estão disponíveis no subconjunto MOCP
    OPERADORES_PROIBIDOS = {
        '++', '--', '+=', '-=', '*=', '/=', '%=',
        '<<', '>>', '&', '|', '^', '~'
    }

    # Mapeamento de palavras-chave do C para equivalente em MOCP
    MAPEAMENTO_C_MOCP = {
        'int': 'inteiro',
        'double': 'real',
        'void': 'vazio',
        'main': 'principal',
        'if': 'se',
        'else': 'senao',
        'while': 'enquanto',
        'for': 'para',
        'return': 'retornar',
        'read': 'ler',
        'readc': 'lerc',
        'reads': 'lers',
        'write': 'escrever',
        'writec': 'escreverc',
        'writev': 'escreverv',
        'writes': 'escrever s'
    }

    def __init__(self):
        # Inicializa o listener e a lista de erros capturados
        super().__init__()
        self.erros = []

    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        """
        Ponto de entrada para tratamento de erros léxicos e sintáticos.
        Analisa a mensagem original do ANTLR e gera uma mensagem adaptada
        com sugestões de correção para a linguagem MOCP.
        """
        simbolo = getattr(offendingSymbol, "text", "(símbolo inválido)")

        # Detecta palavras-chave do C (sempre considerado erro)
        if simbolo in self.PALAVRAS_C_PROIBIDAS:
            sugestao = self.MAPEAMENTO_C_MOCP.get(simbolo, 'equivalente em português')
            mensagem = f"[Erro Sintático] Palavra-chave inválida '{simbolo}' (linha {line}, coluna {column}). Use '{sugestao}'."
            self._registar(mensagem)
            return

        # Detecta operadores proibidos em MOCP
        for op in self.OPERADORES_PROIBIDOS:
            if op in msg or simbolo == op:
                mensagem = f"[Erro Sintático] Operador '{op}' não é suportado na MOCP (linha {line}, coluna {column})."
                self._registar(mensagem)
                return

        # Erro léxico (caracteres inválidos)
        if "token recognition error" in msg:
            match = re.search(r"at:\s*'([^']+)'", msg)
            char_errado = match.group(1) if match else simbolo

            sugestao = ""
            if char_errado == '#':
                sugestao = " Diretivas de pré-processador (#include, #define) não são suportadas."
            elif any(c in char_errado for c in 'áàãâéêíóôõúçÁÀÃÂÉÊÍÓÔÕÚÇ'):
                sugestao = " Identificadores não podem conter acentos."

            mensagem = f"[Erro Léxico] Caractere inválido '{char_errado}' (linha {line}, coluna {column}).{sugestao}"

        # Símbolo inesperado
        elif "extraneous input" in msg:
            sugestao = ""
            if simbolo == ',':
                sugestao = " Verifique os separadores; em 'para' usam-se ';'."
            mensagem = f"[Erro Sintático] Símbolo inesperado '{simbolo}' (linha {line}, coluna {column}).{sugestao}"

        # Nenhuma alternativa válida na gramática
        elif "no viable alternative" in msg:
            mensagem = f"[Erro Sintático] Expressão inválida perto de '{simbolo}' (linha {line}, coluna {column})."

        # Token esperado não encontrado
        elif "missing" in msg:
            esperado = msg.split("missing")[-1].split("at")[0].strip().strip("'")
            esperado_traduzido = traduzir_token_para_portugues(esperado)

            sugestao = ""
            if esperado == 'PONTOVIRG':
                sugestao = " Todas as instruções terminam com ';'."

            mensagem = f"[Erro Sintático] Falta '{esperado_traduzido}' perto de '{simbolo}' (linha {line}, coluna {column}).{sugestao}"

        # Símbolo incompatível com o esperado
        elif "mismatched input" in msg and "expecting" in msg:
            esperados = formatar_esperados(recognizer, e)
            esperados = traduzir_lista_tokens_para_portugues(esperados)

            mensagem = f"[Erro Sintático] Símbolo '{simbolo}' inesperado. Esperado: {esperados} (linha {line}, coluna {column})."

        # Caso genérico
        else:
            mensagem = f"[Erro Sintático] Erro perto de '{simbolo}' (linha {line}, coluna {column}): {msg}"

        self._registar(mensagem)

    def _registar(self, mensagem):
        """
        Regista a mensagem de erro na lista de erros internos e imprime-a.
        """
        self.erros.append(mensagem)
        print(mensagem)


# -------------------------------
# Funções auxiliares
# -------------------------------

def formatar_esperados(recognizer, e):
    """
    Retorna uma lista de tokens esperados pela gramática a partir do objeto de exceção do ANTLR.
    Se não for possível determinar, retorna "desconhecido".
    """
    if not e or not hasattr(e, 'getExpectedTokens'):
        return "desconhecido"

    try:
        expected_token_indexes = list(e.getExpectedTokens())
        expected = []

        for i in expected_token_indexes:
            literal = recognizer.literalNames[i] if i < len(recognizer.literalNames) else None
            symbolic = recognizer.symbolicNames[i] if i < len(recognizer.symbolicNames) else None

            if literal and literal != '<INVALID>':
                expected.append(literal.strip("'\""))
            elif symbolic and symbolic != '<INVALID>':
                expected.append(symbolic)
            else:
                expected.append(f"token_{i}")

        return ', '.join(expected)

    except:
        return "desconhecido"


def traduzir_token_para_portugues(token):
    """
    Traduz tokens internos da gramática para símbolos legíveis ou equivalentes em MOCP.
    """
    mapeamento = {
        'PONTOVIRG': ';',
        'ABREPAR': '(',
        'FECHAPAR': ')',
        'ABRECHAVES': '{',
        'FECHACHAVES': '}',
        'VIRGULA': ',',
        'ATRIBUICAO': '='
    }
    return mapeamento.get(token, token)


def traduzir_lista_tokens_para_portugues(lista_tokens):
    """
    Traduz uma lista de tokens separados por vírgula para a versão em português/símbolos.
    Retorna 'desconhecido' se a lista for inválida ou vazia.
    """
    if not lista_tokens or lista_tokens == "desconhecido":
        return lista_tokens or "desconhecido"

    tokens = lista_tokens.split(', ')
    tokens_traduzidos = [traduzir_token_para_portugues(tok) for tok in tokens]

    return ', '.join(tokens_traduzidos)
