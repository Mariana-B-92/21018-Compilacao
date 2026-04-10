from typing import Any, cast

from MOCPErrorMessages import MOCPErrorMessages
from MOCPParser import MOCPParser
from MOCPSymbolTable import MOCPSymbolTable
from MOCPVisitor import MOCPVisitor
from constants import MAP_C_MOCP

class MOCPSemanticAnalyzer(MOCPVisitor):
    """
    Percorre a Árvore de Sintaxe Abstrata para validar as regras semânticas.
    """
    ERROR = "erro"
    NUMERIC = "numeric"
    STRING_ARRAY = "string_array"

    def __init__(self):
        self.current_declaration_type = None
        self.current_function_type = None
        self.declared_prototypes = set()
        self.errors = []
        self.symbol_table = MOCPSymbolTable()

    # ==========================================
    # 0. MÉTODOS AUXILIARES GERAIS
    # ==========================================

    def _register_error(self, context, message):
        """
        Função auxiliar para adicionar erros formatados com a linha e coluna.
        """
        column = context.start.column
        line = context.start.line

        self.errors.append(f"[Erro Semântico] linha {line}:{column} - {message}")

    def _eval(self, node) -> Any:
        """
        Função auxiliar para avaliar expressões e obter seus tipos.
        """
        return cast(Any, self.visit(node))
    
    def _extract_identifier(self, expr_node):
        """
        Se a expressão for um identificador simples (sem operadores, índices, etc.),
        retorna o nome do identificador. Caso contrário, retorna None.
        """
        if expr_node is None:
            return None

        # Se já for um PrimaryContext, verifica diretamente
        if isinstance(expr_node, MOCPParser.PrimaryContext):
            if expr_node.IDENTIFIER() and not expr_node.LBRACKET():
                return expr_node.IDENTIFIER().getText()
            return None

        # Só desce se houver exatamente 1 filho (sem operadores intermédios)
        if expr_node.getChildCount() == 1:
            return self._extract_identifier(expr_node.getChild(0))

        return None

    # ==========================================
    # 1. PONTO DE ENTRADA (Regra: program)
    # ==========================================

    def visitProgram(self, context: MOCPParser.ProgramContext):
        """
        Regra: program : prototypes body EOF ;
        """

        if context.prototypes():
            self.visit(context.prototypes())

        if context.body():
            self.visit(context.body())

    # ==========================================
    # 2. PROTÓTIPOS
    # ==========================================

    def visitMainPrototype(self, context:MOCPParser.MainPrototypeContext):
        """
        Regra: VOID MAIN LPAREN RPAREN SEMI_COLON
        """
        self.declared_prototypes.add(MAP_C_MOCP.get("main"))

        defined = self.symbol_table.define(
            MAP_C_MOCP.get("main"),
            { "type": MAP_C_MOCP.get("void"), "is_function": True }
        )

        if not defined:
            self._register_error(
                context,
                MOCPErrorMessages.prototype_already_declared(MAP_C_MOCP.get("main"))
            )
        return None

    def visitPrototype(self, context: MOCPParser.PrototypeContext):
        """
        Regra: returnType IDENTIFIER LPAREN parameters? RPAREN SEMI_COLON
        """
        function_name = context.IDENTIFIER().getText()
        function_type = context.returnType().getText()
        self.declared_prototypes.add(function_name)

        # Recolhe os tipos dos parâmetros, se existirem e não forem (void)
        param_types = []
        if context.parameters():
            params = context.parameters()
            if not params.VOID():
                for p in params.parameter():
                    ptype = p.type_().getText()
                    is_array = p.LBRACKET() is not None
                    param_types.append((ptype, is_array))

        defined = self.symbol_table.define(
            function_name,
            {
                "type": function_type,
                "is_function": True,
                "param_types": param_types,
                "is_defined": False,
            },
        )

        if not defined:
            self._register_error(
                context,
                MOCPErrorMessages.prototype_already_declared(function_name)
            )
        return None

    # ==========================================
    # 3. FUNÇÕES E BLOCOS
    # ==========================================

    def visitMainFunction(self, context: MOCPParser.MainFunctionContext):
        """
        Regra: VOID MAIN LPAREN RPAREN block
        """
        main_name = MAP_C_MOCP.get("main")

        # Verifica se o protótipo de 'principal' foi declarado
        if main_name not in self.declared_prototypes:
            self._register_error(context, MOCPErrorMessages.MISSING_MAIN)

        # Verifica se 'principal' já foi definida anteriormente; caso contrário, regista-a
        symbol = self.symbol_table.resolve(main_name)
        if symbol and symbol.get("is_defined", False):
            self._register_error(context, "Função 'principal' já foi definida anteriormente.")
        else:
            self.symbol_table.define(
                main_name,
                {
                    "type": MAP_C_MOCP.get("void"),
                    "is_function": True,
                    "param_types": [],
                    "is_defined": True,
                },
            )

        # Visita o bloco da função num novo âmbito
        self.symbol_table.enter_scope()
        self.visit(context.block())
        self.symbol_table.exit_scope()
        return None

    def visitFunctionDef(self, context: MOCPParser.FunctionDefContext):
        """
        Regra: returnType IDENTIFIER LPAREN parameters? RPAREN block
        """
        function_name = context.IDENTIFIER().getText()
        self.current_function_type = context.returnType().getText()

        # Verifica se o protótipo da função foi previamente declarado
        if function_name not in self.declared_prototypes:
            self._register_error(context, MOCPErrorMessages.prototype_not_declared(function_name))

        # Verifica se a função já foi definida anteriormente
        symbol = self.symbol_table.resolve(function_name)
        if symbol and symbol.get("is_defined", False):
            self._register_error(context, f"Função '{function_name}' já foi definida anteriormente.")

        # Recolhe os tipos dos parâmetros, se existirem e não forem (void)
        param_types = []
        if context.parameters():
            params = context.parameters()
            if not params.VOID():
                for p in params.parameter():
                    ptype = p.type_().getText()
                    is_array = p.LBRACKET() is not None
                    param_types.append((ptype, is_array))

        # Atualiza a definição da função na tabela de símbolos
        self.symbol_table.define(
            function_name,
            {
                "type": self.current_function_type,
                "is_function": True,
                "param_types": param_types,
                "is_defined": True,
            },
        )

        # Visita os parâmetros e o bloco da função num novo âmbito
        self.symbol_table.enter_scope()
        if context.parameters():
            self.visit(context.parameters())
        self.visit(context.block())
        self.symbol_table.exit_scope()

        self.current_function_type = None
        return None

    def visitBlock(self, context: MOCPParser.BlockContext):
        """
        Regra: LBRACE statement* RBRACE
        """
        # O bloco cria sempre um novo âmbito próprio
        self.symbol_table.enter_scope()
        self.visitChildren(context)
        self.symbol_table.exit_scope()
        return None

    # ==========================================
    # 4. DECLARAÇÃO DE VARIÁVEIS
    # ==========================================

    def visitDeclaration(self, context: MOCPParser.DeclarationContext):
        """
        Regra: type variableList SEMI_COLON
        """
        self.current_declaration_type = context.type_().getText()
        self.visit(context.variableList())
        self.current_declaration_type = None
        return None

    def visitVariable(self, context: MOCPParser.VariableContext):
        """
        Regra: IDENTIFIER | IDENTIFIER ASSIGN expression | IDENTIFIER LBRACKET NUMBER RBRACKET | IDENTIFIER LBRACKET RBRACKET ASSIGN READS LPAREN RPAREN
               | IDENTIFIER LBRACKET RBRACKET ASSIGN arrayBlock | IDENTIFIER LBRACKET NUMBER RBRACKET ASSIGN arrayBlock
        """
        variable_name = context.IDENTIFIER().getText()
        is_array = context.LBRACKET() is not None
        decl_type = self.current_declaration_type

        # Se for uma leitura (reads), trata-se como array de inteiros
        if context.READS():
            is_array = True
            if self.current_declaration_type != MAP_C_MOCP.get("int"):
                self._register_error(context, "Variável inicializada com 'lers()' tem de ser do tipo 'inteiro[]'.")
            decl_type = MAP_C_MOCP.get("int")

        # Regista a variável na tabela de símbolos
        defined = self.symbol_table.define(
            variable_name,
            {"type": decl_type, "is_array": is_array, "is_function": False},
        )

        if not defined:
            self._register_error(context, MOCPErrorMessages.variable_already_declared(variable_name))
            return None

        # Verifica a compatibilidade de tipos na inicialização escalar
        if context.expression() and not context.LBRACKET():
            expression_type = self._eval(context.expression())
            if expression_type != self.ERROR and not self._types_compatible_strict(decl_type, expression_type):
                self._register_error(context, MOCPErrorMessages.variable_wrong_type(variable_name))
        
        # Verifica o tamanho e os elementos na inicialização de arrays
        elif context.arrayBlock():
            if context.NUMBER():
                declared_size = int(context.NUMBER().getText())
                array_block = context.arrayBlock()
                if array_block.valueList():
                    num_elements = len(array_block.valueList().expression())
                    if num_elements > declared_size:
                        self._register_error(
                            context,
                            f"Vetor '{variable_name}' declarado com tamanho {declared_size}"
                            f" mas inicializado com {num_elements} elementos.",
                        )
            self.visit(context.arrayBlock())

        return None

    def visitArrayBlock(self, context: MOCPParser.ArrayBlockContext):
        """
        Regra: LBRACE valueList? RBRACE
        """
        # Valida o tipo de cada elemento da lista de valores
        if context.valueList():
            base_type = self.current_declaration_type
            for expression in context.valueList().expression():
                expression_type = self._eval(expression)
                if expression_type != self.ERROR and not self._types_compatible(base_type, expression_type):
                    self._register_error(
                        context,
                        f"Elemento do vetor de tipo incompatível"
                        f" (esperado '{base_type}', recebido '{expression_type}').",
                    )
        return None

    def visitValueList(self, context: MOCPParser.ValueListContext):
        """
        Regra: expression (COMMA expression)*
        """
        for expression in context.expression():
            self._eval(expression)
        return None

    # ==========================================
    # 5. PARÂMETROS DE FUNÇÕES
    # ==========================================

    def visitParameter(self, context: MOCPParser.ParameterContext):
        """
        Regra: type IDENTIFIER | type IDENTIFIER LBRACKET RBRACKET
        """
        parameter_type = context.type_().getText()
        parameter_name = context.IDENTIFIER().getText()
        is_array = context.LBRACKET() is not None
        
        # Regista o parâmetro na tabela de símbolos do âmbito atual
        defined = self.symbol_table.define(
            parameter_name,
            { "type": parameter_type, "is_array": is_array, "is_function": False }
        )
        if not defined:
            self._register_error(context, MOCPErrorMessages.parameter_already_declared(parameter_name))
        return None
        
    # ==========================================
    # 6. EXPRESSÕES E VERIFICAÇÃO DE TIPOS
    # ==========================================

    def visitPrimary(self, context: MOCPParser.PrimaryContext):
        """
        Regra: LPAREN expression RPAREN | functionCall | IDENTIFIER | IDENTIFIER LBRACKET expression RBRACKET | NUMBER | REAL_NUM | STRING_LITERAL
        """
        # Literais numéricos inteiros e reais
        if context.NUMBER(): return MAP_C_MOCP.get("int")
        if context.REAL_NUM(): return MAP_C_MOCP.get("double")

        # Literal de cadeia de caracteres
        if context.STRING_LITERAL(): return self.STRING_ARRAY

        # Expressão entre parênteses: (expression)
        if context.expression() and not context.functionCall() and not context.IDENTIFIER():
            return self._eval(context.expression())

        if context.IDENTIFIER():
            variable_name = context.IDENTIFIER().getText()
            symbol = self.symbol_table.resolve(variable_name)

            # Verifica se a variável foi declarada
            if not symbol:
                self._register_error(context, MOCPErrorMessages.variable_not_declared(variable_name))
                return self.ERROR

            # Verifica se o identificador não é uma função usada como variável
            if symbol.get("is_function"):
                self._register_error(context, MOCPErrorMessages.variable_is_a_function(variable_name))
                return self.ERROR

            # Acesso a elemento de array: IDENTIFIER[expression]
            if context.LBRACKET():
                if not symbol.get("is_array"):
                    self._register_error(context, MOCPErrorMessages.variable_is_not_vector(variable_name))
                    return self.ERROR

                index_type = self._eval(context.expression())
                if not self._is_int(index_type) and index_type != self.ERROR:
                    self._register_error(context, MOCPErrorMessages.ARRAY_INVALID_INDEX)

                return symbol["type"]

            # Variável simples
            return symbol["type"]

        # Chamada de função
        if context.functionCall():
            return self._eval(context.functionCall())

        return self.ERROR

    def visitExpressionAdd(self, context: MOCPParser.ExpressionAddContext):
        """
        Regra: expressionAdd PLUS expressionMul | expressionAdd MINUS expressionMul | expressionMul
        """

       # Sem operador: propaga o tipo do operando
        if not context.PLUS() and not context.MINUS():
            return self._eval(context.expressionMul())

        left_type = self._eval(context.expressionAdd())
        right_type = self._eval(context.expressionMul())

        if left_type == self.ERROR or right_type == self.ERROR:
            return self.ERROR

       # Ambos os operandos têm de ser numéricos
        if not (self._is_numeric(left_type) and self._is_numeric(right_type)):
            self._register_error(context, MOCPErrorMessages.invalid_operation(left_type, right_type))
            return self.ERROR

        # Promoção para double se algum operando for real
        if self._is_real(left_type) or self._is_real(right_type):
            return MAP_C_MOCP.get("double")
        return MAP_C_MOCP.get("int")

    # ==========================================
    # 7. ATRIBUIÇÕES E INSTRUÇÕES
    # ==========================================

    def visitAssignStatement(self, context: MOCPParser.AssignStatementContext):
        """
        Regra: IDENTIFIER ASSIGN expression SEMI_COLON | IDENTIFIER LBRACKET expression RBRACKET ASSIGN expression SEMI_COLON
        """
        variable_name = context.IDENTIFIER().getText()
        symbol = self.symbol_table.resolve(variable_name)

        # Verifica se a variável foi declarada
        if not symbol:
            self._register_error(context, MOCPErrorMessages.variable_not_declared(variable_name))
            return None

        # Verifica se o identificador não é uma função
        if symbol.get("is_function"):
            self._register_error(context, MOCPErrorMessages.variable_is_a_function(variable_name))
            return None

        expressions = context.expression()
        assigned_expression_context = expressions[-1]
        
        # Atribuição a elemento de array: valida índice e tipo
        if context.LBRACKET():
            if not symbol.get("is_array"):
                self._register_error(context, MOCPErrorMessages.variable_is_not_vector(variable_name))
                return None

            index_type = self._eval(expressions[0]) or self.ERROR
            if not self._is_int(index_type) and index_type != self.ERROR:
                self._register_error(context, MOCPErrorMessages.ARRAY_INVALID_INDEX)

        # Atribuição escalar: rejeita uso de array sem índice
        else:
            if symbol.get("is_array"):
                self._register_error(context, MOCPErrorMessages.required_index(variable_name))
                return None

        # Verifica compatibilidade de tipos entre a variável e a expressão atribuída
        expression_type = self._eval(assigned_expression_context)
        if expression_type != self.ERROR and not self._types_compatible_strict(symbol["type"], expression_type):
            self._register_error(context, MOCPErrorMessages.variable_wrong_type(variable_name))
        return None

    # ==========================================
    # 8. CHAMADAS DE FUNÇÃO
    # ==========================================

    def visitFunctionCall(self, context: MOCPParser.FunctionCallContext):
        """
        Regra: IDENTIFIER LPAREN arguments? RPAREN | READ LPAREN RPAREN | READC LPAREN RPAREN | READS LPAREN RPAREN
        """

        # Funções embutidas da linguagem MOCP
        if context.READ():  return self.NUMERIC
        if context.READC(): return MAP_C_MOCP.get("int")
        if context.READS(): return self.STRING_ARRAY

        if context.IDENTIFIER():
            func_name = context.IDENTIFIER().getText()
            symbol = self.symbol_table.resolve(func_name)

            # Verifica se a função foi declarada
            if not symbol:
                self._register_error(context, MOCPErrorMessages.function_not_declared(func_name))
                return self.ERROR

            # Verifica se o identificador é de facto uma função
            if not symbol.get("is_function"):
                self._register_error(context, MOCPErrorMessages.variable_not_a_function(func_name))
                return self.ERROR

            # Recolhe os argumentos passados na chamada
            arg_expressions = []
            if context.arguments():
                arg_expressions = context.arguments().expression()

            # Verifica se o número de argumentos corresponde ao esperado
            expected_params = symbol.get("param_types", [])
            if len(arg_expressions) != len(expected_params):
                self._register_error(
                    context,
                    f"Função '{func_name}' espera {len(expected_params)} argumento(s),"
                    f" mas recebeu {len(arg_expressions)}.",
                )
                for arg in arg_expressions:
                    self._eval(arg)
                return symbol["type"]

            # Verifica o tipo de cada argumento face ao parâmetro esperado
            for i, arg_expression in enumerate(arg_expressions):
                arg_type = self._eval(arg_expression)
                expected_type, expected_is_array = expected_params[i]

                if arg_type == self.ERROR:
                    continue

                if expected_is_array:
                    variable_name = self._extract_identifier(arg_expression)
                    if variable_name:
                        variable_symbol = self.symbol_table.resolve(variable_name)
                        if variable_symbol and not variable_symbol.get("is_array", False):
                            self._register_error(
                                context,
                                f"Argumento {i + 1} da função '{func_name}' deve ser um vetor.",
                            )
                    elif arg_type != self.STRING_ARRAY:
                        self._register_error(
                            context,
                            f"Argumento {i + 1} da função '{func_name}' deve ser um vetor,"
                            f" mas recebeu tipo '{arg_type}'.",
                        )
                else:
                    # O argumento deve ser compatível com o tipo escalar esperado
                    if not self._types_compatible(expected_type, arg_type):
                        self._register_error(
                            context,
                            f"Argumento {i + 1} da função '{func_name}' é do tipo '{arg_type}',"
                            f" mas esperava '{expected_type}'.",
                        )

            return symbol["type"]

        return self.ERROR
        
    # ==========================================
    # 9. RESTANTES EXPRESSÕES E PRECEDÊNCIAS
    # ==========================================

    def visitExpressionOr(self, context: MOCPParser.ExpressionOrContext):
        """
        Regra: expressionOr OR expressionAnd | expressionAnd
        """
        # Sem operador: propaga o tipo do operando
        if context.OR() is None:
            return self._eval(context.expressionAnd())

        left_type = self._eval(context.expressionOr())
        right_type = self._eval(context.expressionAnd())

        # Ambos os operandos têm de ser numéricos
        if left_type != self.ERROR and right_type != self.ERROR:
            if not (self._is_numeric(left_type) and self._is_numeric(right_type)):
                self._register_error(context, MOCPErrorMessages.invalid_operation(left_type, right_type))

        # Operações lógicas resultam sempre num inteiro (0 ou 1)
        return MAP_C_MOCP.get("int")

    def visitExpressionAnd(self, context: MOCPParser.ExpressionAndContext):
        """
        Regra: expressionAnd AND expressionEquality | expressionEquality
        """
        # Sem operador: propaga o tipo do operando
        if context.AND() is None:
            return self._eval(context.expressionEquality())

        left_type = self._eval(context.expressionAnd())
        right_type = self._eval(context.expressionEquality())

        # Ambos os operandos têm de ser numéricos
        if left_type != self.ERROR and right_type != self.ERROR:
            if not (self._is_numeric(left_type) and self._is_numeric(right_type)):
                self._register_error(context, MOCPErrorMessages.invalid_operation(left_type, right_type))

        # Operações lógicas resultam sempre num inteiro (0 ou 1)
        return MAP_C_MOCP.get("int")
        
    def visitExpressionMul(self, context: MOCPParser.ExpressionMulContext):
        """ 
        Regra: expressionMul MULT expressionUnary | expressionMul DIV expressionUnary | expressionMul MOD expressionUnary | expressionUnary
        """
        # Sem operador: propaga o tipo do operando
        if not context.MULT() and not context.DIV() and not context.MOD():
            return self._eval(context.expressionUnary())

        left_type = self._eval(context.expressionMul())
        right_type = self._eval(context.expressionUnary())

        if left_type == self.ERROR or right_type == self.ERROR:
            return self.ERROR

        # Regra de C/MOCP: O módulo (%) só pode ser aplicado a inteiros
        if context.MOD():
            if not (self._is_int(left_type) and self._is_int(right_type)):
                self._register_error(context, MOCPErrorMessages.MOD_ONLY_FOR_INTEGERS)
                return self.ERROR
            return MAP_C_MOCP.get("int")

        # Multiplicação e divisão requerem operandos numéricos
        if not (self._is_numeric(left_type) and self._is_numeric(right_type)):
            self._register_error(context, MOCPErrorMessages.invalid_operation(left_type, right_type))
            return self.ERROR

        # Promoção para double se algum operando for real
        if self._is_real(left_type) or self._is_real(right_type):
            return MAP_C_MOCP.get("double")
        return MAP_C_MOCP.get("int")

    def visitExpressionEquality(self, context: MOCPParser.ExpressionEqualityContext):
        """
        Regra: == | !=
        """
        # Sem operador: propaga o tipo do operando
        if not context.equalityOp():
            return self._eval(context.expressionRelational())

        left_type = self._eval(context.expressionEquality())
        right_type = self._eval(context.expressionRelational())

        # Ambos os operandos têm de ser numéricos
        if left_type != self.ERROR and right_type != self.ERROR:
            if not (self._is_numeric(left_type) and self._is_numeric(right_type)):
                self._register_error(context, MOCPErrorMessages.invalid_operation(left_type, right_type))

        # Comparações de igualdade resultam num inteiro (0 ou 1)
        return MAP_C_MOCP.get("int")

    def visitExpressionRelational(self, context: MOCPParser.ExpressionRelationalContext):
        """
        Regra: expressionAdd relationalOp expressionAdd | expressionAdd
        """
        # Sem operador: propaga o tipo do operando
        if not context.relationalOp():
            return self._eval(context.expressionAdd(0))

        left_type = self._eval(context.expressionAdd(0))
        right_type = self._eval(context.expressionAdd(1))

        # Ambos os operandos têm de ser numéricos
        if left_type != self.ERROR and right_type != self.ERROR:
            if not (self._is_numeric(left_type) and self._is_numeric(right_type)):
                self._register_error(context, MOCPErrorMessages.INVALID_RELATIONAL_OPERATORS)

        # Comparações relacionais resultam num inteiro (0 ou 1)
        return MAP_C_MOCP.get("int")

    def visitExpressionUnary(self, context: MOCPParser.ExpressionUnaryContext):
        """
        Regra: ! | - | (cast)
        """
        # Negação lógica: operando tem de ser numérico; resultado é inteiro
        if context.NOT():
            expression_type = self._eval(context.expressionUnary())
            if not self._is_numeric(expression_type) and expression_type != self.ERROR:
                self._register_error(context, MOCPErrorMessages.invalid_operation_for_type(expression_type))
            return MAP_C_MOCP.get("int")

        # Negação aritmética: operando tem de ser numérico; preserva o tipo
        if context.MINUS():
            expression_type = self._eval(context.expressionUnary())
            if not self._is_numeric(expression_type) and expression_type != self.ERROR:
                self._register_error(context, MOCPErrorMessages.invalid_operation_for_type(expression_type))
            return expression_type

        return self._eval(context.castExpr())

    def visitCastExpr(self, context: MOCPParser.CastExprContext):
        """
        Regra: LPAREN type RPAREN castExpr | primary
        """
        if context.type_():
            target_type = context.type_().getText()

            # Cast só é permitido para tipos numéricos
            if target_type not in [MAP_C_MOCP.get("int"), MAP_C_MOCP.get("double")]:
                self._register_error(context, "Cast só pode ser para 'inteiro' ou 'real'.")
                return self.ERROR

            # A expressão de origem também tem de ser numérica
            source_type = self._eval(context.castExpr())
            if not self._is_numeric(source_type) and source_type != self.ERROR:
                self._register_error(context, "Cast só pode ser aplicado a expressões numéricas.")
                return self.ERROR

            return target_type

        return self._eval(context.primary())

    # ==========================================
    # 10. INSTRUÇÕES DE CONTROLO E CICLOS
    # ==========================================

    def visitStatement(self, context: MOCPParser.StatementContext):
        """
        Regra: IF LPAREN expression RPAREN block (ELSE block)? | whileStatement | forStatement | returnStatement | assignStatement | expressionStatement | declaration | block
        """
        if context.IF():
            # A condição do IF tem de ser numérica
            condition_type = self._eval(context.expression())
            if not self._is_numeric(condition_type) and condition_type != self.ERROR:
                self._register_error(context, MOCPErrorMessages.IF_CONDITION_NOT_NUMERICAL)

            # Visita o bloco then e, se existir, o bloco else
            for block in context.block():
                self.visit(block)
            return None

        self.visitChildren(context)
        return None

    def visitWhileStatement(self, context: MOCPParser.WhileStatementContext):
        """
        Regra: WHILE LPAREN expression RPAREN block
        """
        # A condição do WHILE tem de ser numérica
        condition_type = self._eval(context.expression())
        if not self._is_numeric(condition_type) and condition_type != self.ERROR:
            self._register_error(context, MOCPErrorMessages.WHILE_CONDITION_NOT_NUMERICAL)

        self.visit(context.block())
        return None

    def visitForStatement(self, context: MOCPParser.ForStatementContext):
        """
        Regra: FOR LPAREN expressionOrAssign? SEMI_COLON expression? SEMI_COLON expressionOrAssign? RPAREN block
        """
        # Inicialização do ciclo
        if context.expressionOrAssign(0):
            self._eval(context.expressionOrAssign(0))

        # A condição do FOR tem de ser numérica
        if context.expression():
            condition_type = self._eval(context.expression())
            if not self._is_numeric(condition_type) and condition_type != self.ERROR:
                self._register_error(context, MOCPErrorMessages.FOR_CONDITION_NOT_NUMERICAL)

        # Incremento/atualização do ciclo
        if context.expressionOrAssign(1):
            self._eval(context.expressionOrAssign(1))

        self.visit(context.block())
        return None

    def visitExpressionOrAssign(self, context: MOCPParser.ExpressionOrAssignContext):
        """
        Regra: IDENTIFIER (LBRACKET expression RBRACKET)? ASSIGN expression | expression
        """
        # Distingue entre uma atribuição e uma expressão simples
        if context.ASSIGN():
            self._visit_assign_in_for(context)
        else:
            self._eval(context.expression())
        return None

    def _visit_assign_in_for(self, context: MOCPParser.ExpressionOrAssignContext):
        variable_name = context.IDENTIFIER().getText()
        symbol = self.symbol_table.resolve(variable_name)

        if not symbol:
            self._register_error(context, MOCPErrorMessages.variable_not_declared(variable_name))
            return None

        if symbol.get("is_function"):
            self._register_error(context, MOCPErrorMessages.variable_is_a_function(variable_name))
            return None

        # Se for uma atribuição a um elemento de array
        if context.LBRACKET():
            if not symbol.get("is_array"):
                self._register_error(context, MOCPErrorMessages.variable_is_not_vector(variable_name))
            else:
                # O primeiro 'expression' é o índice
                index_expr = context.expression(0)
                if index_expr:
                    index_type = self._eval(index_expr)
                    if not self._is_int(index_type) and index_type != self.ERROR:
                        self._register_error(context, MOCPErrorMessages.ARRAY_INVALID_INDEX)

        # Obter a expressão do lado direito (último elemento da lista de expressões)
        expr_list = context.expression()
        assigned_expr = expr_list[-1] if expr_list else None

        if not assigned_expr:
            self._register_error(context, "Expressão de atribuição inválida no ciclo 'para'.")
            return None

        expression_type = self._eval(assigned_expr)
        if expression_type != self.ERROR and not self._types_compatible_strict(symbol["type"], expression_type):
            self._register_error(context, MOCPErrorMessages.variable_wrong_type(variable_name))

        return None    

    # ==========================================
    # 11. INSTRUÇÕES DE ENTRADA / SAÍDA (MOCP)
    # ==========================================

    def visitWriteStatement(self, context: MOCPParser.WriteStatementContext):
        """
        Regra: WRITE LPAREN expression RPAREN SEMI_COLON | WRITEC LPAREN expression RPAREN SEMI_COLON | WRITEV LPAREN IDENTIFIER RPAREN SEMI_COLON
               | WRITES LPAREN stringArgument RPAREN SEMI_COLON
        """
        if context.WRITE() or context.WRITEC():
            expression_type = self._eval(context.expression()) or self.ERROR

            # WRITE aceita qualquer tipo, mas não strings (arrays de caracteres)
            if context.WRITE() and expression_type == self.STRING_ARRAY:
                self._register_error(context, "Função 'escrever()' não aceita strings. Use 'escrevers()'.")

            # WRITEC exige um inteiro (escreve um único carácter)
            if context.WRITEC() and not self._is_int(expression_type) and expression_type != self.ERROR:
                self._register_error(context, MOCPErrorMessages.WRITEC_INVALID_TYPE)

        elif context.WRITEV():
            # WRITEV exige um identificador que seja um array
            variable_name = context.IDENTIFIER().getText()
            symbol = self.symbol_table.resolve(variable_name)
            if not symbol:
                self._register_error(context, MOCPErrorMessages.array_not_declared(variable_name))
            elif not symbol.get("is_array"):
                self._register_error(context, MOCPErrorMessages.write_c_not_vector(variable_name))

        elif context.WRITES():
            # WRITES escreve uma cadeia de caracteres
            self._eval(context.stringArgument())

        return None

    def visitStringArgument(self, context: MOCPParser.StringArgumentContext):
        """
        Regra: STRING_LITERAL | IDENTIFIER
        """
        if context.IDENTIFIER():
            # Se for um identificador, tem de ser um array (cadeia de caracteres)
            variable_name = context.IDENTIFIER().getText()
            symbol = self.symbol_table.resolve(variable_name)
            if not symbol:
                self._register_error(context, MOCPErrorMessages.array_not_declared(variable_name))
            elif not symbol.get("is_array"):
                self._register_error(context, MOCPErrorMessages.WRITES_INVALID_TYPE)

        return None

    # ==========================================
    # 12. RETORNO DE FUNÇÕES
    # ==========================================

    def visitReturnStatement(self, context: MOCPParser.ReturnStatementContext):
        """
        Regra: RETURN expression? SEMI_COLON
        """
        # Assume retorno void se não houver expressão
        return_type = MAP_C_MOCP.get("void")
        if context.expression():
            return_type = self._eval(context.expression())

        # Função void não pode retornar um valor
        if self.current_function_type == MAP_C_MOCP.get("void") and return_type != MAP_C_MOCP.get("void"):
            self._register_error(context, MOCPErrorMessages.RETURN_TYPE_VOID)

        # Função não-void tem de retornar um valor
        elif self.current_function_type != MAP_C_MOCP.get("void") and return_type == MAP_C_MOCP.get("void"):
            self._register_error(context, MOCPErrorMessages.unexpected_return_type(self.current_function_type))

        # Promoção implícita de double para int é permitida (sem erro)
        elif self.current_function_type == MAP_C_MOCP.get("int") and return_type == MAP_C_MOCP.get("double"):
            pass

        return None

    # ==========================================
    # 13. FUNÇÕES AUXILIARES PARA TIPOS
    # ==========================================

    def _types_compatible(self, expected, actual):
        """
        Verifica se os tipos são compatíveis, considerando regras de promoção e casos especiais.
        """
        if actual == self.ERROR:
            return True
        if expected == actual:
            return True
        if expected == MAP_C_MOCP.get("int") and actual == MAP_C_MOCP.get("double"):
            return True
        if expected == MAP_C_MOCP.get("double") and actual == MAP_C_MOCP.get("int"):
            return True
        if actual == self.NUMERIC:
            return expected in [MAP_C_MOCP.get("int"), MAP_C_MOCP.get("double")]
        if actual == self.STRING_ARRAY and expected == MAP_C_MOCP.get("int"):
            return True
        return False
    
    def _types_compatible_strict(self, expected, actual):
        """
        Versão estrita para atribuições — segue as regras do C:
        - inteiro -> real é permitido (promoção implícita)
        - real -> inteiro NÃO é permitido sem cast explícito
        """
        if actual == self.ERROR:
            return True
        if expected == actual:
            return True
        if expected == MAP_C_MOCP.get("double") and actual == MAP_C_MOCP.get("int"):
            return True  # promoção implícita inteiro -> real
        if actual == self.NUMERIC:
            return expected in [MAP_C_MOCP.get("int"), MAP_C_MOCP.get("double")]
        if actual == self.STRING_ARRAY and expected == MAP_C_MOCP.get("int"):
            return True
        return False
    
    def _is_numeric(self, t):
        """
        Retorna True se o tipo for numérico (inteiro, real ou numérico).
        """
        return t in [MAP_C_MOCP.get("int"), MAP_C_MOCP.get("double"), self.NUMERIC]

    def _is_int(self, t):
        """
        Retorna True se o tipo for inteiro ou numérico.
        """
        return t in [MAP_C_MOCP.get("int"), self.NUMERIC]

    def _is_real(self, t):
        """
        Retorna True se o tipo for real (double).
        """
        return t == MAP_C_MOCP.get("double")
