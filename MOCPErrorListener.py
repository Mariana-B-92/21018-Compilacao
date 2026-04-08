from antlr4.error.ErrorListener import ErrorListener
import re
from constants import FORBIDDEN_C_OPERATORS, FORBIDDEN_C_WORDS, MAP_C_MOCP
from utils import format_expected, translate_token, translate_tokens_list

class MOCPErrorListener(ErrorListener):
    """
    Listener responsável por capturar e adaptar erros do ANTLR para a linguagem MOCP.
    Traduz mensagens de erro léxico e sintático em sugestões amigáveis.
    """

    def __init__(self):
        """
        Inicializa o listener e a lista de erros capturados.
        """
        super().__init__()
        self.errors = []

    def _register(self, message):
        """
        Regista a mensagem de erro na lista de erros internos.
        """
        self.errors.append(message)

    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        """
        Ponto de entrada para tratamento de erros léxicos e sintáticos.
        Analisa a mensagem original do ANTLR e gera uma mensagem adaptada
        com sugestões de correção para a linguagem MOCP.
        """
        symbol = getattr(offendingSymbol, "text", "(símbolo inválido)")
        suggestion, message = "", ""


        # Deteta palavras-chave do C (sempre considerado erro):
        if symbol in FORBIDDEN_C_WORDS:
            suggestion = MAP_C_MOCP.get(symbol, 'equivalente em português')
            message = f"[Erro Sintático] Palavra-chave inválida '{symbol}' (linha {line}, coluna {column}). Use '{suggestion}'."

        # Deteta operadores proibidos em MOCP:
        elif symbol in FORBIDDEN_C_OPERATORS:
            message = f"[Erro Sintático] Operador '{symbol}' não é suportado na MOCP (linha {line}, coluna {column})."

        # Erro léxico (caracteres inválidos):
        elif "token recognition error" in msg:
            match = re.search(r"at:\s*'([^']+)'", msg)
            wrong_char = match.group(1) if match else symbol

            if wrong_char == '#':
                suggestion = "Diretivas de pré-processador (#include, #define) não são suportadas."
            elif any(char in wrong_char for char in 'áàãâéêíóôõúçÁÀÃÂÉÊÍÓÔÕÚÇ'):
                suggestion = "Identificadores não podem conter acentos."

            message = f"[Erro Léxico] Caractere inválido '{wrong_char}' (linha {line}, coluna {column}). {suggestion}"

        # Símbolo inesperado:
        elif "extraneous input" in msg:
            if symbol == ',':
                suggestion = " Verifique os separadores; em 'para' usam-se ';'."

            message = f"[Erro Sintático] Símbolo inesperado '{symbol}' (linha {line}, coluna {column}). {suggestion}"

        # Nenhuma alternativa válida na gramática:
        elif "no viable alternative" in msg:
            message = f"[Erro Sintático] Expressão inválida perto de '{symbol}' (linha {line}, coluna {column})."

        # Token esperado não encontrado:
        elif "missing" in msg:
            expected = msg.split("missing")[-1].split("at")[0].strip().strip("'")
            translated_expected = translate_token(expected)

            if expected == 'SEMI_COLON':
                suggestion = "Todas as instruções terminam com ';'."

            message = f"[Erro Sintático] Falta '{translated_expected}' perto de '{symbol}' (linha {line}, coluna {column}). {suggestion}"

        # Símbolo incompatível com o esperado:
        elif "mismatched input" in msg and "expecting" in msg:
            expected = format_expected(recognizer, e)
            translated_expected = translate_tokens_list(expected)

            message = f"[Erro Sintático] Símbolo '{symbol}' inesperado. Esperado: {translated_expected} (linha {line}, coluna {column})."

        # Caso genérico:
        else:
            message = f"[Erro Sintático] Erro perto de '{symbol}' (linha {line}, coluna {column}): {msg}"

        self._register(message)
