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
        Regra:
            IDENTIFIER
        | IDENTIFIER ASSIGN expression
        | IDENTIFIER LBRACKET NUMBER RBRACKET
        | IDENTIFIER LBRACKET RBRACKET ASSIGN READS LPAREN RPAREN
        | IDENTIFIER LBRACKET RBRACKET ASSIGN arrayBlock
        | IDENTIFIER LBRACKET NUMBER RBRACKET ASSIGN arrayBlock
        """
        variable_name = context.IDENTIFIER().getText()
        is_array = context.LBRACKET() is not None
        decl_type = self.current_declaration_type

        # Se for uma leitura (reads), trata-se como array de inteiros
        if context.READS():
            is_array = True
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
            expr_type = self._eval(context.expression())
            if expr_type != self.ERROR and not self._types_compatible(decl_type, expr_type):
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
            for expr in context.valueList().expression():
                expr_type = self._eval(expr)
                if expr_type != self.ERROR and not self._types_compatible(base_type, expr_type):
                    self._register_error(
                        context,
                        f"Elemento do vetor de tipo incompatível"
                        f" (esperado '{base_type}', recebido '{expr_type}').",
                    )
        return None

    def visitValueList(self, context: MOCPParser.ValueListContext):
        """
        Regra: expression (COMMA expression)*
        """
        for expr in context.expression():
            self._eval(expr)
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
        Regra: LPAREN expression RPAREN | functionCall | IDENTIFIER
            | IDENTIFIER LBRACKET expression RBRACKET
            | NUMBER | REAL_NUM | STRING_LITERAL
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
            var_name = context.IDENTIFIER().getText()
            symbol = self.symbol_table.resolve(var_name)

            # Verifica se a variável foi declarada
            if not symbol:
                self._register_error(context, MOCPErrorMessages.variable_not_declared(var_name))
                return self.ERROR

            # Verifica se o identificador não é uma função usada como variável
            if symbol.get("is_function"):
                self._register_error(context, MOCPErrorMessages.variable_is_a_function(var_name))
                return self.ERROR

            # Acesso a elemento de array: IDENTIFIER[expression]
            if context.LBRACKET():
                if not symbol.get("is_array"):
                    self._register_error(context, MOCPErrorMessages.variable_is_not_vector(var_name))
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
        Regra: expressionAdd PLUS expressionMul
            | expressionAdd MINUS expressionMul
            | expressionMul
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
        Regra: IDENTIFIER ASSIGN expression SEMI_COLON
            | IDENTIFIER LBRACKET expression RBRACKET ASSIGN expression SEMI_COLON
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
        if expression_type != self.ERROR and not self._types_compatible(symbol["type"], expression_type):
            self._register_error(context, MOCPErrorMessages.variable_wrong_type(variable_name))
        return None

    # ==========================================
    # 8. CHAMADAS DE FUNÇÃO
    # ==========================================

    def visitFunctionCall(self, context: MOCPParser.FunctionCallContext):
        """
        Regra: IDENTIFIER (arguments?) | READ () | READC () | READS ()
        """

        # 1. Funções Embutidas do MOCP
        if context.READ() or context.READC(): return MAP_C_MOCP.get("int")
        if context.READS(): return "string"

        # 2. Funções definidas pelo utilizador
        function_name = context.IDENTIFIER().getText()
        symbol = self.symbol_table.resolve(function_name)

        if not symbol:
            self._register_error(context, MOCPErrorMessages.function_not_declared(function_name))
            return self.ERROR

        if not symbol.get("is_function"):
            self._register_error(context, MOCPErrorMessages.variable_not_a_function(function_name))
            return self.ERROR

        # Visita os argumentos passados (para garantir que variáveis usadas lá dentro existem, etc.)
        if context.arguments():
            self.visit(context.arguments())

        return symbol["type"]

    def visitArguments(self, context: MOCPParser.ArgumentsContext):
        """
        Regra: expression, expression
        """
        for expression in context.expression():
            self.visit(expression)

    # ==========================================
    # 9. RESTANTES EXPRESSÕES E PRECEDÊNCIAS
    # ==========================================

    def visitExpressionMul(self, context: MOCPParser.ExpressionMulContext):
        """
        Regra: expressionMul (MULT | DIV | MOD) expressionUnary | expressionUnary
        """
        if not context.MULT() and not context.DIV() and not context.MOD():
            return self.visit(context.expressionUnary())

        left_type = self.visit(context.expressionMul())
        right_type = self.visit(context.expressionUnary())

        if left_type == self.ERROR or right_type == self.ERROR:
            return self.ERROR

        # Regra de C/MOCP: O módulo (%) só pode ser aplicado a inteiros
        if context.MOD():
            if left_type != MAP_C_MOCP.get("int") or right_type != MAP_C_MOCP.get("int"):
                self._register_error(context, MOCPErrorMessages.MOD_ONLY_FOR_INTEGERS)
                return self.ERROR

            return MAP_C_MOCP.get("int")

        # Coerção para multiplicação e divisão
        if left_type == MAP_C_MOCP.get("double") or right_type == MAP_C_MOCP.get("double"):
            return MAP_C_MOCP.get("double")

        return MAP_C_MOCP.get("int")

    def visitExpressionEquality(self, context: MOCPParser.ExpressionEqualityContext):
        """
        Regra: == | !=
        """
        if not context.equalityOp():
            return self.visit(context.expressionRelational())

        self.visit(context.expressionEquality())
        self.visit(context.expressionRelational())

        # Em C, a igualdade retorna 0 ou 1 (inteiro)
        return MAP_C_MOCP.get("int")

    def visitExpressionRelational(self, context: MOCPParser.ExpressionRelationalContext):
        """
        Regra: < | <= | > | >=
        """
        if not context.relationalOp():
            return self.visit(context.expressionAdd())

        left_type = self.visit(context.expressionRelational())
        right_type = self.visit(context.expressionAdd())

        if left_type != self.ERROR and right_type != self.ERROR:
            allowed_types = [MAP_C_MOCP.get("int"), MAP_C_MOCP.get("double")]

            if left_type not in allowed_types or right_type not in allowed_types:
                self._register_error(context, MOCPErrorMessages.INVALID_RELATIONAL_OPERATORS)

        # Em C, comparações resultam num inteiro
        return MAP_C_MOCP.get("int")

    def visitExpressionUnary(self, context: MOCPParser.ExpressionUnaryContext):
        """
        Regra: ! | - | (cast)
        """
        if context.NOT():
            self.visit(context.expressionUnary())
            return MAP_C_MOCP.get("int")

        if context.MINUS():
            expression_type = self.visit(context.expressionUnary())

            if expression_type not in [MAP_C_MOCP.get("int"), MAP_C_MOCP.get("double"), self.ERROR]:
                self._register_error(context, MOCPErrorMessages.invalid_operation_for_type(expression_type))

            return expression_type

        return self.visit(context.castExpr())

    def visitCastExpr(self, context: MOCPParser.CastExprContext):
        """
        Regra: (cast)
        """
        if context.type_():
            new_type = context.type_().getText()
            self.visit(context.castExpr())
            return new_type

        return self.visit(context.primary())

    # ==========================================
    # 10. INSTRUÇÕES DE CONTROLO E CICLOS
    # ==========================================

    def visitStatement(self, context: MOCPParser.StatementContext):
        """
        Regra: IF (expression) block (ELSE block)? | whileStatement | forStatement | returnStatement | assignStatement
        | expressionStatement | declaration | block
        """

        if context.IF():
            condition_type = self.visit(context.expression())

            if condition_type not in [MAP_C_MOCP.get("int"), MAP_C_MOCP.get("double"), self.ERROR]:
                self._register_error(context, MOCPErrorMessages.IF_CONDITION_NOT_NUMERICAL)

            for block in context.block():
                self.visit(block)

            return

        self.visitChildren(context)

    def visitWhileStatement(self, context: MOCPParser.WhileStatementContext):
        condition_type = self.visit(context.expression())

        if condition_type not in [MAP_C_MOCP.get("int"), MAP_C_MOCP.get("double"), self.ERROR]:
            self._register_error(context, MOCPErrorMessages.WHILE_CONDITION_NOT_NUMERICAL)

        self.visit(context.block())

    def visitForStatement(self, context: MOCPParser.ForStatementContext):
        # Visita a inicialização e atualização (se existirem)
        for expression_or_assignment in context.expressionOrAssign():
            self.visit(expression_or_assignment)

        # Visita a condição do meio (se existir)
        if context.expression():
            condition_type = self.visit(context.expression())

            if condition_type not in [MAP_C_MOCP.get("int"), MAP_C_MOCP.get("double"), self.ERROR]:
                self._register_error(context, MOCPErrorMessages.FOR_CONDITION_NOT_NUMERICAL)

        self.visit(context.block())

    # ==========================================
    # 11. INSTRUÇÕES DE ENTRADA / SAÍDA (MOCP)
    # ==========================================

    def visitWriteStatement(self, context: MOCPParser.WriteStatementContext):
        """
        Regra: WRITE(expression); | WRITEC(expression); | WRITEV(id); | WRITES(stringArg);
        """
        if context.WRITE() or context.WRITEC():
            expression_type = self.visit(context.expression())

            if context.WRITEC() and expression_type != MAP_C_MOCP.get("int") and expression_type != self.ERROR:
                self._register_error(context,MOCPErrorMessages.WRITEC_INVALID_TYPE)

        elif context.WRITEV():
            variable_name = context.IDENTIFIER().getText()
            symbol = self.symbol_table.resolve(variable_name)

            if not symbol:
                self._register_error(context, MOCPErrorMessages.array_not_declared(variable_name))
            elif not symbol.get("is_array"):
                self._register_error(context,MOCPErrorMessages.write_c_not_vector(variable_name))

        elif context.WRITES():
            argument_context = context.stringArgument()

            if argument_context.IDENTIFIER():
                variable_name = argument_context.IDENTIFIER().getText()
                symbol = self.symbol_table.resolve(variable_name)

                if not symbol:
                    self._register_error(context, MOCPErrorMessages.array_not_declared(variable_name))
                elif not symbol.get("is_array"):
                    self._register_error(context,MOCPErrorMessages.WRITES_INVALID_TYPE)

    # ==========================================
    # 12. RETORNO DE FUNÇÕES
    # ==========================================

    def visitReturnStatement(self, context: MOCPParser.ReturnStatementContext):
        return_type = MAP_C_MOCP.get("void")

        if context.expression():
            return_type = self.visit(context.expression())

        if self.current_function_type == MAP_C_MOCP.get("void") and return_type != MAP_C_MOCP.get("void"):
            self._register_error(context, MOCPErrorMessages.RETURN_TYPE_VOID)
        elif self.current_function_type != MAP_C_MOCP.get("void") and return_type == MAP_C_MOCP.get("void"):
            self._register_error(context,MOCPErrorMessages.unexpected_return_type(self.current_function_type))
        elif self.current_function_type == MAP_C_MOCP.get("int") and return_type == MAP_C_MOCP.get("double"):
            self._register_error(context, MOCPErrorMessages.RETURN_TYPE_INVALID)
