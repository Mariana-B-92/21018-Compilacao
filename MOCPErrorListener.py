import re
from antlr4.error.ErrorListener import ErrorListener
from constants import MAP_C_MOCP
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
        symbol_text = getattr(offendingSymbol, "text", "(símbolo inválido)")
        token_type_name = ""
        if offendingSymbol is not None:
            try:
                idx = offendingSymbol.type
                token_type_name = recognizer.symbolicNames[idx] if idx < len(recognizer.symbolicNames) else ""
            except Exception:
                token_type_name = ""

        suggestion, message = "", ""

        is_lexer_error = "token recognition error" in msg

        # Suprime erros de EOF em cascata se já houver erros registados
        if symbol_text == '<EOF>' and self.errors:
            return

        # Supressão de erros sintáticos em cascata
        if not is_lexer_error and (line in self._lex_error_lines or self._has_unrecoverable_lex_error):
            return

        # ── Palavras-chave proibidas de C (FORBIDDEN_KEYWORD) ──────────────────
        # São agora reconhecidas pelo léxico como token próprio, pelo que chegam
        # aqui como erros sintáticos ("mismatched input" ou "extraneous input")
        # com o tipo FORBIDDEN_KEYWORD. Tratamo-las imediatamente como erros léxicos.
        if token_type_name == "FORBIDDEN_KEYWORD":
            suggestion_word = MAP_C_MOCP.get(symbol_text)
            tipos_proibidos = {"char", "float", "long", "short", "signed", "unsigned"}
            if suggestion_word:
                message = (
                    f"[Erro Léxico] Palavra-chave de C proibida '{symbol_text}' "
                    f"(linha {line}, coluna {column}). Use '{suggestion_word}'."
                )
            elif symbol_text in tipos_proibidos:
                message = (
                    f"[Erro Léxico] Tipo de C proibido '{symbol_text}' "
                    f"(linha {line}, coluna {column}). Apenas existem os tipos 'inteiro' e 'real'."
                )
            else:
                message = (
                    f"[Erro Léxico] Palavra-chave de C proibida '{symbol_text}' "
                    f"(linha {line}, coluna {column}). Esta palavra não tem equivalente em MOCP."
                )
            self._lex_error_lines.add(line)
            self._register(message)
            return

        # ── Operadores proibidos ───────────────────────────────────────────────
        # São tokens do léxico que chegam ao parser como símbolos não esperados.
        # Tratamo-los como erros léxicos para que o diagnóstico seja imediato e claro.
        if token_type_name == "FORBIDDEN_OPERATOR":
            message = (
                f"[Erro Léxico] Operador '{symbol_text}' não é suportado na MOCP "
                f"(linha {line}, coluna {column})."
            )

            self._lex_error_lines.add(line)
            self._register(message)
            return

        # Erro léxico (caracteres inválidos):
        if is_lexer_error:
            match = re.search(r"at:\s*'([^']+)'", msg)
            wrong_char = match.group(1) if match else symbol_text

            if wrong_char == '#':
                suggestion = "Diretivas de pré-processador (#include, #define) não são suportadas."
                self._has_unrecoverable_lex_error = True
            elif any(char in wrong_char for char in 'áàãâéêíóôõúçÁÀÃÂÉÊÍÓÔÕÚÇ'):
                suggestion = "Identificadores não podem conter acentos."

            self._lex_error_lines.add(line)
            message = f"[Erro Léxico] Caractere inválido '{wrong_char}' (linha {line}, coluna {column}). {suggestion}"

        # Símbolo inesperado:
        elif "extraneous input" in msg:
            if symbol_text == ',':
                suggestion = " Verifique os separadores; em 'para' usam-se ';'."
            message = f"[Erro Sintático] Símbolo inesperado '{symbol_text}' (linha {line}, coluna {column}). {suggestion}"

        # Nenhuma alternativa válida na gramática:
        elif "no viable alternative" in msg:
            message = f"[Erro Sintático] Expressão inválida perto de '{symbol_text}' (linha {line}, coluna {column})."

        # Token esperado não encontrado:
        elif "missing" in msg:
            expected = msg.split("missing")[-1].split("at")[0].strip().strip("'")
            translated_expected = translate_token(expected)

            if expected == 'SEMI_COLON':
                suggestion = "Todas as instruções terminam com ';'."
            elif expected == '{':
                suggestion = "Todos os blocos devem estar entre chavetas { }, mesmo quando têm uma só instrução."

            message = f"[Erro Sintático] Falta '{translated_expected}' perto de '{symbol_text}' (linha {line}, coluna {column}). {suggestion}"

        # Símbolo incompatível com o esperado:
        elif "mismatched input" in msg and "expecting" in msg:
            expected = format_expected(recognizer, e)
            translated_expected = translate_tokens_list(expected)

            if symbol_text in ('<', '<=', '>', '>=', '==', '!=') and ')' in expected:
                message = f"[Erro Sintático] Condição inválida: não é permitido encadear operadores relacionais (linha {line}, coluna {column}). As condições devem ser da forma 'Expr OpCond Expr'."
            else:
                message = f"[Erro Sintático] Símbolo '{symbol_text}' inesperado. Esperado: {translated_expected} (linha {line}, coluna {column})."

        self._register(message)