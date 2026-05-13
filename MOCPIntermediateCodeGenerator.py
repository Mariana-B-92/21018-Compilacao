from MOCPParser import MOCPParser
from MOCPVisitor import MOCPVisitor

class MOCPIntermediateCodeGenerator(MOCPVisitor):
    def __init__(self, symbol_table):
        self.symbol_table = symbol_table
        self.code = []
        self.temp_count = 0
        self.label_count = 0

    # ==========================================
    # 0. MÉTODOS AUXILIARES GERAIS
    # ==========================================

    def generate_new_temp(self):
        self.temp_count += 1
        return f"t{self.temp_count}"

    def generate_new_label(self):
        self.label_count += 1
        return f"L{self.label_count}"

    def emit(self, instruction):
        self.code.append(instruction)

    # ==========================================
    # 1. FUNÇÕES
    # ==========================================

    def visitMainFunction(self, context: MOCPParser.MainFunctionContext):
        """
        Regra: VOID MAIN LPAREN RPAREN block
        """

        main_name = context.MAIN().getText()

        # Emite o rótulo do ponto de entrada do programa
        self.emit(f"{main_name}:")

        # Visita o bloco da função principal
        self.visit(context.block())
        return None

    def visitFunctionDef(self, context: MOCPParser.FunctionDefContext):
        """
        Regra: returnType IDENTIFIER LPAREN parameters? RPAREN block
        """

        function_name = context.IDENTIFIER().getText()

        self.emit(f"{function_name}:")
        self.visit(context.block())

        return None

    # ==========================================
    # 2. DECLARAÇÃO DE VARIÁVEIS
    # ==========================================

    def visitVariable(self, context: MOCPParser.VariableContext):
        """
        Regra: IDENTIFIER | IDENTIFIER ASSIGN expression | IDENTIFIER LBRACKET NUMBER RBRACKET | IDENTIFIER LBRACKET RBRACKET ASSIGN READS LPAREN RPAREN
               | IDENTIFIER LBRACKET RBRACKET ASSIGN arrayBlock | IDENTIFIER LBRACKET NUMBER RBRACKET ASSIGN arrayBlock
        """
        variable_name = context.IDENTIFIER().getText()

        # Se a variável for inicializada na declaração (ex: inteiro m = 1;)
        if context.ASSIGN():
            if context.expression():
                expression = self.visit(context.expression())
                self.emit(f"{variable_name} = {expression}")

            elif context.READS():
                temp = self.generate_new_temp()
                self.emit(f"{temp} = call lers, 0")
                self.emit(f"{variable_name} = {temp}")

        return None

    # ==========================================
    # 3. EXPRESSÕES E VERIFICAÇÃO DE TIPOS
    # ==========================================

    def visitPrimary(self, context:MOCPParser.PrimaryContext):
        """
        Regra: LPAREN expression RPAREN | functionCall | IDENTIFIER | IDENTIFIER LBRACKET expression RBRACKET | NUMBER | REAL_NUM | STRING_LITERAL
        """

        # Acesso a Vetor: IDENTIFIER[expression]
        if context.IDENTIFIER() and context.LBRACKET():
            array_name = context.IDENTIFIER().getText()

            index_expression = self.visit(context.expression())

            # Consulta o tamanho na tabela de símbolos para calcular o offset
            symbol = self.symbol_table.resolve(array_name)
            width = 8 if symbol and symbol.get("type") == "real" else 4

            # Cria um temporário para calcular o offset (índice * largura)
            offset = self.generate_new_temp()
            self.emit(f"{offset} = {index_expression} * {width}")

            # Lê o valor do vetor na memória para um novo temporário de resultado
            result_temp = self.generate_new_temp()
            self.emit(f"{result_temp} = {array_name}[{offset}]")

            return result_temp

        # Variável simples: IDENTIFIER
        elif context.IDENTIFIER():
            return context.IDENTIFIER().getText()

        # Expressão entre parênteses: (expression)
        elif context.LPAREN() and context.expression():
            return self.visit(context.expression())

        # Literais
        elif context.NUMBER():
            return context.NUMBER().getText()
        elif context.REAL_NUM():
            return context.REAL_NUM().getText()
        elif context.STRING_LITERAL():
            return context.STRING_LITERAL().getText()

        # Chamada de função
        elif context.functionCall():
            return self.visit(context.functionCall())

        return None

    def visitExpressionAdd(self, context: MOCPParser.ExpressionAddContext):
        """
        Regra: expressionAdd PLUS expressionMul | expressionAdd MINUS expressionMul | expressionMul
        """

        # Se só tem um filho, é apenas a passagem para o nível inferior de precedência
        if context.getChildCount() == 1:
            return self.visit(context.getChild(0))

        left = self.visit(context.getChild(0))
        right = self.visit(context.getChild(2))
        operator = context.getChild(1).getText()

        # Gerar temporário e emitir instrução TAC
        temp = self.generate_new_temp()
        self.emit(f"{temp} = {left} {operator} {right}")

        return temp

    # ==========================================
    # 4. ATRIBUIÇÕES E INSTRUÇÕES
    # ==========================================

    def visitAssignStatement(self, context: MOCPParser.AssignStatementContext):
        """
        Regra: IDENTIFIER ASSIGN expression SEMI_COLON | IDENTIFIER LBRACKET expression RBRACKET ASSIGN expression SEMI_COLON
        """

        variable_name = context.IDENTIFIER().getText()

        # Tratar apenas de atribuições a variáveis simples, sem vetores
        if context.LBRACKET() is None:
            # Visita a expressão à direita do '=' para obter o seu endereço final/temporário
            expression = self.visit(context.expression(0))

            # Emite a instrução final de atribuição
            self.emit(f"{variable_name} = {expression}")
        else:
            # Lógica para atribuições a vetores: x[i] = y
            # Obtém as duas expressões envolvidas:
            # expression(0) é o índice 'i', expression(1) é o valor 'y'
            index = self.visit(context.expression(0))
            value = self.visit(context.expression(1))

            # Consultamos o tipo da variável na tabela de símbolos para saber a largura.
            # Se não estiver declarada, assumimos um valor seguro (ex: 4).
            symbol = self.symbol_table.resolve(variable_name)
            width = 8 if symbol and symbol.get("type") == "real" else 4

            # Cria um temporário para calcular o offset (índice * largura)
            offset = self.generate_new_temp()
            self.emit(f"{offset} = {index} * {width}")

            # Emite a instrução final de atribuição indexada ao vetor
            self.emit(f"{variable_name}[{offset}] = {value}")
            pass

        return None

    # ==========================================
    # 5. CHAMADAS DE FUNÇÃO
    # ==========================================

    def visitFunctionCall(self, context: MOCPParser.FunctionCallContext):
        """
        Regra: IDENTIFIER LPAREN arguments? RPAREN | READ LPAREN RPAREN | READC LPAREN RPAREN | READS LPAREN RPAREN
        """

        # Identificar o nome da função e os argumentos
        args_context = None
        function_name = None

        if context.IDENTIFIER():
            function_name = context.IDENTIFIER().getText()
            args_context = context.arguments()
        elif context.READ():
            function_name = "ler"
        elif context.READC():
            function_name = "lerc"
        elif context.READS():
            function_name = "lers"

        args = []

        # Visitar e recolher o endereço de cada argumento (E1, E2, ..., En)
        if args_context:
            for expression in args_context.expression():
                args.append(self.visit(expression))

        # Emitir instrução 'param' para cada argumento
        for arg in args:
            self.emit(f"param {arg}")

        num_args = len(args)
        temp = self.generate_new_temp()

        # Emitir instrução call que atribui o valor de retorno ao temporário
        self.emit(f"{temp} = call {function_name}, {num_args}")

        return temp

    # ==========================================
    # 6. RESTANTES EXPRESSÕES E PRECEDÊNCIAS
    # ==========================================

    def visitExpressionOr(self, context: MOCPParser.ExpressionOrContext):
        """
        Regra: expressionOr OR expressionAnd | expressionAnd
        """
        if context.getChildCount() == 1:
            return self.visit(context.getChild(0))

        left = self.visit(context.getChild(0))
        right = self.visit(context.getChild(2))
        operator = context.getChild(1).getText()

        temp = self.generate_new_temp()
        self.emit(f"{temp} = {left} {operator} {right}")
        return temp

    def visitExpressionOrAssign(self, context: MOCPParser.ExpressionOrAssignContext):
        """
        Regra: IDENTIFIER (LBRACKET expression RBRACKET)? ASSIGN expression | expression
        """

        # Se for uma atribuição (ex: i = 0 ou i = i + 1)
        if context.ASSIGN():
            variable_name = context.IDENTIFIER().getText()

            # Se for uma atribuição simples
            if context.LBRACKET() is None:
                expression = self.visit(context.expression(0))
                self.emit(f"{variable_name} = {expression}")

            # Se for uma atribuição a um vetor (x[i] = y)
            else:
                index = self.visit(context.expression(0))
                value = self.visit(context.expression(1))

                symbol = self.symbol_table.resolve(variable_name)
                width = 8 if symbol and symbol.get("type") == "real" else 4

                offset = self.generate_new_temp()
                self.emit(f"{offset} = {index} * {width}")
                self.emit(f"{variable_name}[{offset}] = {value}")

            return None

        # Se for apenas uma expressão sem atribuição
        return self.visit(context.expression(0))

    def visitExpressionAnd(self, context: MOCPParser.ExpressionAndContext):
        """
        Regra: expressionAnd AND expressionEquality | expressionEquality
        """

        if context.getChildCount() == 1:
            return self.visit(context.getChild(0))

        left = self.visit(context.getChild(0))
        right = self.visit(context.getChild(2))
        operator = context.getChild(1).getText()

        temp = self.generate_new_temp()
        self.emit(f"{temp} = {left} {operator} {right}")
        return temp

    def visitExpressionMul(self, context: MOCPParser.ExpressionMulContext):
        """
        Regra: expressionMul MULT expressionUnary | expressionMul DIV expressionUnary | expressionMul MOD expressionUnary | expressionUnary
        """

        if context.getChildCount() == 1:
            return self.visit(context.getChild(0))

        left = self.visit(context.getChild(0))
        right = self.visit(context.getChild(2))
        operator = context.getChild(1).getText()

        temp = self.generate_new_temp()
        self.emit(f"{temp} = {left} {operator} {right}")

        return temp

    def visitExpressionEquality(self, context: MOCPParser.ExpressionEqualityContext):
        """
        Regra: == | !=
        """

        if context.getChildCount() == 1:
            return self.visit(context.getChild(0))

        left = self.visit(context.getChild(0))
        right = self.visit(context.getChild(2))
        operator = context.getChild(1).getText()

        temp = self.generate_new_temp()
        self.emit(f"{temp} = {left} {operator} {right}")
        return temp

    def visitExpressionRelational(self, context: MOCPParser.ExpressionRelationalContext):
        """
        Regra: expressionAdd relationalOp expressionAdd | expressionAdd
        """

        if context.getChildCount() == 1:
            return self.visit(context.getChild(0))

        left = self.visit(context.getChild(0))
        right = self.visit(context.getChild(2))
        operator = context.getChild(1).getText()

        temp = self.generate_new_temp()
        self.emit(f"{temp} = {left} {operator} {right}")
        return temp

    def visitExpressionUnary(self, context: MOCPParser.ExpressionUnaryContext):
        """
        Regra: ! | - | (cast)
        """

        if context.getChildCount() == 1:
            return self.visit(context.getChild(0))

        # O operador unário é o primeiro filho: '!' ou '-'
        operator = context.getChild(0).getText()
        expression = self.visit(context.getChild(1))

        temp = self.generate_new_temp()

        if operator == '-':
            # Usamos 'minus' para distinguir da subtração binária
            self.emit(f"{temp} = minus {expression}")
        elif operator == '!':
            self.emit(f"{temp} = not {expression}")

        return temp

    def visitCastExpr(self, context: MOCPParser.CastExprContext):
        """
        Regra: LPAREN type RPAREN castExpr | primary
        """

        if context.getChildCount() == 1:
            return self.visit(context.getChild(0))

        # O tipo do cast está no índice 1: '(' type ')' castExpr
        cast_type = context.getChild(1).getText()
        expression = self.visit(context.getChild(3))

        temp = self.generate_new_temp()

        self.emit(f"{temp} = ({cast_type}) {expression}")
        return temp

    # ==========================================
    # 6. INSTRUÇÕES DE CONTROLO E CICLOS
    # ==========================================

    def visitStatement(self, context: MOCPParser.StatementContext):
        """
        Regra: IF LPAREN expression RPAREN block (ELSE block)? | whileStatement | forStatement | returnStatement | assignStatement | expressionStatement | declaration | block
        """

        if context.IF():
            # Avalia a expressão da condição (ex: t1 = x > y)
            condition = self.visit(context.expression())

            label_false = self.generate_new_label()
            label_end = self.generate_new_label()

            # Desvio condicional: se a condição for falsa, salta para label_false
            self.emit(f"ifFalse {condition} goto {label_false}")

            # Visita o código do bloco IF (verdadeiro)
            self.visit(context.block(0))

            if context.ELSE():
                # Se tiver ELSE, o bloco IF precisa de saltar o bloco ELSE no final
                self.emit(f"goto {label_end}")
                self.emit(f"{label_false}:")

                # Visita o código do bloco ELSE
                self.visit(context.block(1))
                self.emit(f"{label_end}:")
            else:
                # Se não tiver ELSE, a label_false serve apenas para marcar o fim do IF
                self.emit(f"{label_false}:")
            return None

        # Para as outras alternativas da regra (enquanto, para, etc.),
        # deixamos o ANTLR descer automaticamente para as regras específicas.
        return self.visitChildren(context)

    def visitWhileStatement(self, context:MOCPParser.WhileStatementContext):
        """
        Regra: WHILE LPAREN expression RPAREN block
        """
        label_begin = self.generate_new_label()
        label_end = self.generate_new_label()

        # Marca o início do ciclo
        self.emit(f"{label_begin}:")

        # Avalia a condição no início de cada iteração
        condition = self.visit(context.expression())

        # Se a condição falhar, sai do ciclo
        self.emit(f"ifFalse {condition} goto {label_end}")

        # Visita o corpo do ciclo
        self.visit(context.block())

        # No fim do corpo, salta incondicionalmente de volta para o início
        self.emit(f"goto {label_begin}")

        # Marca a saída do ciclo
        self.emit(f"{label_end}:")

        return None

    def visitForStatement(self, context: MOCPParser.ForStatementContext):
        """
        Regra: FOR LPAREN expressionOrAssign? SEMI_COLON expression? SEMI_COLON expressionOrAssign? RPAREN block
        """

        initializer_node = None
        condition_node = None
        update_node = None

        assign_idx = 0
        passed_first_semi = False
        passed_second_semi = False

        for i in range(context.getChildCount()):
            child = context.getChild(i)

            if child.getText() == ';':
                if not passed_first_semi:
                    passed_first_semi = True
                else:
                    passed_second_semi = True
            elif isinstance(child, MOCPParser.ExpressionOrAssignContext):
                if not passed_first_semi:
                    initializer_node = child
                else:
                    update_node = child
            elif isinstance(child, MOCPParser.ExpressionContext):
                condition_node = child

        # --- Criação de TAC ---

        # Inicialização
        if initializer_node:
            self.visit(initializer_node)

        label_begin = self.generate_new_label()
        label_end = self.generate_new_label()

        # Início do Ciclo
        self.emit(f"{label_begin}:")

        # Condição
        if condition_node:
            condition = self.visit(condition_node)
            self.emit(f"ifFalse {condition} goto {label_end}")

        # Corpo do Ciclo
        self.visit(context.block())

        # Atualização
        if update_node:
            self.visit(update_node)

        # Voltar ao início e marcar o fim
        self.emit(f"goto {label_begin}")
        self.emit(f"{label_end}:")

        return None

    # ==========================================
    # 7. INSTRUÇÕES DE ENTRADA / SAÍDA (MOCP)
    # ==========================================

    def visitWriteStatement(self, context: MOCPParser.WriteStatementContext):
        """
        Regra: WRITE LPAREN expression RPAREN SEMI_COLON | WRITEC LPAREN expression RPAREN SEMI_COLON | WRITEV LPAREN IDENTIFIER RPAREN SEMI_COLON
               | WRITES LPAREN stringArgument RPAREN SEMI_COLON
        """

        if context.WRITE() or context.WRITEC():
            function_name = "escrever" if context.WRITE() else "escreverc"
            expression = self.visit(context.expression())
            self.emit(f"param {expression}")
            self.emit(f"call {function_name}, 1")

        elif context.WRITEV():
            array_name = context.IDENTIFIER().getText()
            self.emit(f"param {array_name}")
            self.emit("call escreverv, 1")

        elif context.WRITES():
            string_arg = context.stringArgument().getText()
            self.emit(f"param {string_arg}")
            self.emit("call escrevers, 1")

        return None

    # ==========================================
    # 8. RETORNO DE FUNÇÕES
    # ==========================================

    def visitReturnStatement(self, context: MOCPParser.ReturnStatementContext):
        """
        Regra: RETURN expression? SEMI_COLON
        """

        # Se retornar um valor, calcula a expressão primeiro
        if context.expression():
            expression = self.visit(context.expression())
            self.emit(f"return {expression}")
        else:
            self.emit("return")

        return None
