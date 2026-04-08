from constants import MAP_MOCP_SYMBOLS

def format_expected(recognizer, e):
    """
    Retorna uma lista de tokens esperados pela gramática a partir do objeto de exceção do ANTLR.
    Se não for possível determinar, retorna "desconhecido".
    """
    if not e or not hasattr(e, 'getExpectedTokens'):
        return "desconhecido"

    try:
        expected_token_indexes = list(e.getExpectedTokens())
        expected = []

        for index in expected_token_indexes:
            literal = recognizer.literalNames[index] if index < len(recognizer.literalNames) else None
            symbolic = recognizer.symbolicNames[index] if index < len(recognizer.symbolicNames) else None

            if literal and literal != '<INVALID>':
                expected.append(literal.strip("'\""))
            elif symbolic and symbolic != '<INVALID>':
                expected.append(symbolic)
            else:
                expected.append(f"token_{index}")

        return ', '.join(expected)

    except:
        return "desconhecido"


def translate_token(token):
    """
    Traduz tokens internos da gramática para símbolos legíveis ou equivalentes em MOCP.
    """
    return MAP_MOCP_SYMBOLS.get(token, token)


def translate_tokens_list(tokens_list):
    """
    Traduz uma lista de tokens separados por vírgula para a versão em português/símbolos.
    Retorna 'desconhecido' se a lista for inválida ou vazia.
    """
    if not tokens_list or tokens_list == "desconhecido":
        return tokens_list or "desconhecido"

    tokens = tokens_list.split(', ')
    translated_tokens = [translate_token(token) for token in tokens]

    return ', '.join(translated_tokens)
