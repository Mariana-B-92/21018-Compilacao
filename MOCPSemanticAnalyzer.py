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
        if MAP_C_MOCP.get("main") not in self.declared_prototypes:
            self._register_error(context, MOCPErrorMessages.MISSING_MAIN)

        self.symbol_table.enter_scope()
        self.visit(context.block())
        self.symbol_table.exit_scope()

    def visitFunctionDef(self, context: MOCPParser.FunctionDefContext):
        """
        Regra: returnType IDENTIFIER LPAREN parameters? RPAREN block
        """
        function_name = context.IDENTIFIER().getText()
        self.current_function_type = context.returnType().getText()

        if function_name not in self.declared_prototypes:
            self._register_error(context, MOCPErrorMessages.prototype_not_declared(function_name))

        self.symbol_table.enter_scope()
        if context.parameters(): self.visit(context.parameters())
        self.visit(context.block())
        self.symbol_table.exit_scope()

    def visitBlock(self, context: MOCPParser.BlockContext):
        """
        Regra: LBRACE statement* RBRACE
        """
        self.symbol_table.enter_scope()
        self.visitChildren(context)
        self.symbol_table.exit_scope()

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

    def visitVariable(self, context: MOCPParser.VariableContext):
        """
        Regra: IDENTIFIER | IDENTIFIER=expression | IDENTIFIER[number] | IDENTIFIER[]=() | IDENTIFIER[]=[] | IDENTIFIER[number]=[]
        """
        variable_name = context.IDENTIFIER().getText()
        is_array = context.LBRACKET() is not None

        defined = self.symbol_table.define(
            variable_name,
            { "type": self.current_declaration_type, "is_array": is_array, "is_function": False}
        )

        if not defined:
            self._register_error(context, MOCPErrorMessages.variable_already_declared(variable_name))

        # Se a variável estiver a ser inicializada (tem uma expressão ou um arrayBlock associado),
        # pelo que delegamos a visita a esses nós para futura verificação de tipos.
        if context.expression():
            self.visit(context.expression())

        if context.arrayBlock():
            self.visit(context.arrayBlock())

    # ==========================================
    # 5. PARÂMETROS DE FUNÇÕES
    # ==========================================

    def visitParameter(self, context: MOCPParser.ParameterContext):
        """
        Regra: IDENTIFIER? | IDENTIFIER?[]
        """
        parameter_type = context.type_().getText()
        is_array = context.LBRACKET() is not None

        if not context.IDENTIFIER():
            self._register_error(context, MOCPErrorMessages.UNIDENTIFIED_PARAMETERS)
            return

        parameter_name = context.IDENTIFIER().getText()

        defined = self.symbol_table.define(
            parameter_name,
            { "type": parameter_type, "is_array": is_array, "is_function": False }
        )

        if not defined:
            self._register_error(context, MOCPErrorMessages.parameter_already_declared(parameter_name))

    # ==========================================
    # 6. EXPRESSÕES E VERIFICAÇÃO DE TIPOS
    # ==========================================

    def visitPrimary(self, context: MOCPParser.PrimaryContext):
        """
        Regra: (expression) | functionCall | IDENTIFIER | IDENTIFIER[expression] | NUMBER | REAL_NUM | STRING_LITERAL
        """

        # 1. Literais Numéricos
        if context.NUMBER(): return MAP_C_MOCP.get("int")
        if context.REAL_NUM(): return MAP_C_MOCP.get("double")

        # 2. Strings
        if context.STRING_LITERAL(): return "string"

        if context.IDENTIFIER():
            variable_name = context.IDENTIFIER().getText()
            symbol = self.symbol_table.resolve(variable_name)

            # 3. Variável Simples (Apenas IDENTIFIER, sem parenteses retos ou chamadas de função)
            if not context.LBRACKET():
                if not symbol:
                    self._register_error(context, MOCPErrorMessages.variable_not_declared(variable_name))
                    return self.ERROR
                elif symbol.get("is_function"):
                    self._register_error(context, MOCPErrorMessages.variable_is_a_function(variable_name))
                    return self.ERROR
                else:
                    return symbol["type"]

            # 4. Acesso a Vetor (IDENTIFIER[expression])
            if context.LBRACKET():
                if not symbol:
                    self._register_error(context, MOCPErrorMessages.array_not_declared(variable_name))
                    return self.ERROR
                elif not symbol.get("is_array"):
                    self._register_error(context, MOCPErrorMessages.variable_is_not_vector(variable_name))

                index_type = self.visit(context.expression())

                if index_type != "inteiro" and index_type != self.ERROR:
                    self._register_error(context, MOCPErrorMessages.ARRAY_INVALID_INDEX)

                return symbol["type"]

        # 5. Chamada de Função
        if context.functionCall():
            return self.visit(context.functionCall())

        # 6. Expressão entre parênteses: ( expressao )
        if context.expression() and context.LPAREN():
            return self.visit(context.expression())

        return self.ERROR

    def visitExpressionAdd(self, context: MOCPParser.ExpressionAddContext):
        """
        Regra: expressionAdd PLUS expressionMul | expressionAdd MINUS expressionMul | expressionMul
        """

        # Se for apenas a passagem para a próxima regra de precedência:
        if not context.PLUS() and not context.MINUS():
            return self.visit(context.expressionMul())

        left_type = self.visit(context.expressionAdd())
        right_type = self.visit(context.expressionMul())

        if left_type == self.ERROR or right_type == self.ERROR:
            return self.ERROR

        allowed_types = [MAP_C_MOCP.get("int"), MAP_C_MOCP.get("double")]

        if left_type not in allowed_types or right_type not in allowed_types:
            self._register_error(context, MOCPErrorMessages.invalid_operation(left_type, right_type))
            return self.ERROR

        if left_type == MAP_C_MOCP.get("double") or right_type == MAP_C_MOCP.get("double"):
            return MAP_C_MOCP.get("double")

        return MAP_C_MOCP.get("int")

    # ==========================================
    # 7. ATRIBUIÇÕES E INSTRUÇÕES
    # ==========================================

    def visitAssignStatement(self, context: MOCPParser.AssignStatementContext):
        """
        Regra: (IDENTIFIER | IDENTIFIER [expression]) = expression;
        """
        variable_name = context.IDENTIFIER().getText()
        symbol = self.symbol_table.resolve(variable_name)

        if not symbol:
            self._register_error(context, MOCPErrorMessages.variable_not_declared(variable_name))
            return self.ERROR

        if symbol.get("is_function"):
            self._register_error(context, MOCPErrorMessages.variable_is_a_function(variable_name))
            return self.ERROR

        expressions = context.expression()
        assigned_expression_context = expressions[-1]

        expression_type = self.visit(assigned_expression_context)

        if expression_type != self.ERROR:
            variable_type = symbol["type"]

            if variable_type == MAP_C_MOCP.get("int") and expression_type == MAP_C_MOCP.get("double"):
                self._register_error(context,MOCPErrorMessages.variable_wrong_type(variable_name))

        if context.LBRACKET():
            if not symbol.get("is_array"):
                self._register_error(context, MOCPErrorMessages.variable_is_not_vector(variable_name))
            else:
                index_expression_context = expressions
                index_type = self.visit(index_expression_context)

                if index_type != MAP_C_MOCP.get("int") and index_type != self.ERROR:
                    self._register_error(context, MOCPErrorMessages.ARRAY_INVALID_INDEX)
        elif symbol.get("is_array"):
            self._register_error(context, MOCPErrorMessages.required_index(variable_name))

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
