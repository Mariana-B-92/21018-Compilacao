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

    def update(self, name, attributes):
        """
        Atualiza os atributos de um símbolo já existente, procurando-o do escopo
        mais interno para o mais externo (mesma ordem que resolve()). Os atributos
        fornecidos são fundidos com os existentes (os novos sobrepõem-se).
        Devolve True se o símbolo foi encontrado e atualizado, False caso contrário.

        Esta operação é necessária para casos como a passagem de protótipo para
        definição de função, onde o símbolo já existe e precisa de ter atributos
        como 'is_defined' atualizados de False para True.
        """
        for scope in reversed(self.scopes):
            if name in scope:
                scope[name].update(attributes)
                return True
        return False

    def resolve(self, name):
        """
        Procura um símbolo do escopo mais interno para o mais externo.
        """
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]

        return None