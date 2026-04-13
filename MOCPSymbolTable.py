class MOCPSymbolTable:
    """
    Gere os símbolos (variáveis e funções) e os escopos do programa.
    Usa uma pilha de dicionários, onde o índice 0 é o escopo global.
    """

    def __init__(self):
        self.scopes=[{}]

    def enter_scope(self):
        """
        Cria um novo escopo local (ex: quando entra num ciclo ou função).
        """
        self.scopes.append({})

    def exit_scope(self):
        """
        Destroi o escopo atual (ex: quando encontra um bloco com '}').
        """
        self.scopes.pop()

    def define(self, name, attributes):
        """
        Define um novo símbolo no escopo atual.
        Retorna False se o símbolo já existir.
        """
        if name in self.scopes[-1]:
            return False

        self.scopes[-1][name] = attributes
        return True

    def resolve(self, name):
        """
        Procura um símbolo do escopo mais interno para o mais externo.
        """
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]

        return None
