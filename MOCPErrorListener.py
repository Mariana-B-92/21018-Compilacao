import re
from antlr4.error.ErrorListener import ErrorListener
from constants import FORBIDDEN_C_OPERATORS, FORBIDDEN_C_WORDS, MAP_C_MOCP
from utils import format_expected, translate_token, translate_tokens_list

class MOCPErrorListener(ErrorListener):
    """
    Listener responsável por capturar e adaptar erros do ANTLR para a linguagem MOCP.
    Traduz mensagens de erro léxico e sintático em sugestões amigáveis.
    """

    def __init__(self):
        super().__init__()
        self.errors = []
        self._lex_error_lines = set()
        self._has_unrecoverable_lex_error = False

    def _register(self, message):
        self.errors.append(message)

    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        symbol = getattr(offendingSymbol, "text", "(símbolo inválido)")
        suggestion, message = "", ""

        is_lexer_error = "token recognition error" in msg

        # Suprime erros de EOF em cascata se já houver erros registados
        if symbol == '<EOF>' and self.errors:
            return

        # Supressão de erros sintáticos em cascata
        if not is_lexer_error and (line in self._lex_error_lines or self._has_unrecoverable_lex_error):
            return

        # Deteta palavras-chave do C:
        if symbol in FORBIDDEN_C_WORDS:
            suggestion = MAP_C_MOCP.get(symbol)
            if suggestion:
                message = f"[Erro Sintático] Palavra-chave inválida '{symbol}' (linha {line}, coluna {column}). Use '{suggestion}'."
            else:
                message = f"[Erro Sintático] Palavra-chave inválida '{symbol}' (linha {line}, coluna {column}). Apenas existem os tipos 'inteiro' e 'real'."

        # Deteta operadores proibidos em MOCP:
        elif symbol in FORBIDDEN_C_OPERATORS:
            message = f"[Erro Sintático] Operador '{symbol}' não é suportado na MOCP (linha {line}, coluna {column})."

        # Erro léxico (caracteres inválidos):
        elif is_lexer_error:
            match = re.search(r"at:\s*'([^']+)'", msg)
            wrong_char = match.group(1) if match else symbol

            if wrong_char == '#':
                suggestion = "Diretivas de pré-processador (#include, #define) não são suportadas."
                self._has_unrecoverable_lex_error = True
            elif any(char in wrong_char for char in 'áàãâéêíóôõúçÁÀÃÂÉÊÍÓÔÕÚÇ'):
                suggestion = "Identificadores não podem conter acentos."

            self._lex_error_lines.add(line)
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
            elif expected == '{':
                suggestion = "Todos os blocos devem estar entre chavetas { }, mesmo quando têm uma só instrução."

            message = f"[Erro Sintático] Falta '{translated_expected}' perto de '{symbol}' (linha {line}, coluna {column}). {suggestion}"

        # Símbolo incompatível com o esperado:
        elif "mismatched input" in msg and "expecting" in msg:
            expected = format_expected(recognizer, e)
            translated_expected = translate_tokens_list(expected)

            if symbol in ('<', '<=', '>', '>=', '==', '!=') and ')' in expected:
                message = f"[Erro Sintático] Condição inválida: não é permitido encadear operadores relacionais (linha {line}, coluna {column}). As condições devem ser da forma 'Expr OpCond Expr'."
            else:
                message = f"[Erro Sintático] Símbolo '{symbol}' inesperado. Esperado: {translated_expected} (linha {line}, coluna {column})."

        self._register(message)
