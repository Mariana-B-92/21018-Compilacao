from MOCPParser import MOCPParser
from MOCPVisitor import MOCPVisitor


class MOCPIntermediateCodeGenerator(MOCPVisitor):
    """
    Gera código intermédio TAC (Three Address Code) a partir da árvore sintática MOCP.
    Cada instrução é representada como uma quádrupla estruturada:
        {"op": str, "arg1": str|None, "arg2": str|None, "res": str|None}
    """

    def __init__(self, symbol_table):
        self.symbol_table = symbol_table
        self.quadruplos = []
        self.temp_count = 0
        self.label_count = 0

    def visit(self, tree):
        if tree is None:
            return None
        return tree.accept(self)

    # ==========================================
    # 0. MÉTODOS AUXILIARES
    # ==========================================

    def generate_new_temp(self):
        """Gera um novo temporário único (t1, t2, ...)."""
        self.temp_count += 1
        return f"t{self.temp_count}"

    def generate_new_label(self):
        """Gera um novo label único (L1, L2, ...)."""
        self.label_count += 1
        return f"L{self.label_count}"

    def emit(self, op, arg1=None, arg2=None, res=None):
        """
        Adiciona uma quádrupla à lista.
        Para operações que produzem valor, gera automaticamente um temporário
        se nenhum resultado for fornecido.
        """
        ops_sem_resultado = {
            "label", "goto", "ifFalse", "return", "halt",
            "param", "write", "writec", "writev",
            "writes", "alloc", "[]="
        }
        if res is None and op not in ops_sem_resultado:
            res = self.generate_new_temp()

        self.quadruplos.append({"op": op, "arg1": arg1, "arg2": arg2, "res": res})
        return res

    def _extract_identifier(self, expr_node):
        """
        Percorre o nó de expressão em busca de um IDENTIFIER simples.
        Usado por WRITEV para obter o nome do vetor sem gerar temporários.
        Retorna None se a expressão não for um identificador direto.
        """
        if expr_node is None:
            return None
        if isinstance(expr_node, MOCPParser.PrimaryContext):
            if expr_node.IDENTIFIER() and expr_node.LBRACKET() is None:
                return expr_node.IDENTIFIER().getText()
            return None
        if expr_node.getChildCount() == 1:
            return self._extract_identifier(expr_node.getChild(0))
        return None

    def get_code_as_strings(self):
        """
        Converte as quádruplas para uma lista de strings legíveis.
        _fmt() trata valores Python produzidos pelo otimizador:
            True/False → "1"/"0",  None → ""
        """

        def _fmt(v):
            if isinstance(v, bool):
                return "1" if v else "0"
            if v is None:
                return ""
            return str(v)

        lines = []
        for q in self.quadruplos:
            op  = q["op"]
            a1  = q.get("arg1")
            a2  = q.get("arg2")
            res = q.get("res")

            if op == "label":
                lines.append(f"{res}:")
            elif op == "goto":
                lines.append(f"goto {res}")
            elif op == "ifFalse":
                lines.append(f"ifFalse {_fmt(a1)} goto {res}")
            elif op == "=":
                lines.append(f"{res} = {_fmt(a1)}")
            elif op in {"+", "-", "*", "/", "%", "==", "!=", "<", "<=", ">", ">=", "&&", "||"}:
                lines.append(f"{res} = {_fmt(a1)} {op} {_fmt(a2)}")
            elif op == "minus":
                lines.append(f"{res} = -{_fmt(a1)}")
            elif op == "not":
                lines.append(f"{res} = !{_fmt(a1)}")
            elif op == "cast":
                lines.append(f"{res} = ({a1}) {_fmt(a2)}")
            elif op == "[]":
                lines.append(f"{res} = {a1}[{_fmt(a2)}]")
            elif op == "[]=":
                lines.append(f"{res}[{_fmt(a1)}] = {_fmt(a2)}")
            elif op == "alloc":
                lines.append(f"alloc {res}, {a1}")
            elif op == "param":
                lines.append(f"param {_fmt(a1)}")
            elif op == "call":
                lines.append(f"{res} = call {a1}, {a2}")
            elif op == "return":
                lines.append(f"return {_fmt(a1)}" if a1 is not None else "return")
            elif op == "halt":
                lines.append("halt")
            elif op == "write":
                lines.append(f"write {_fmt(a1)}")
            elif op == "writec":
                lines.append(f"writec {_fmt(a1)}")
            elif op == "writev":
                lines.append(f"writev {a1}")
            elif op == "writes":
                lines.append(f"writes {a1}")
            else:
                lines.append(str(q))
        return lines

    # ==========================================
    # 1. FUNÇÕES
    # ==========================================

    def visitMainFunction(self, context: MOCPParser.MainFunctionContext):
        """Emite o label 'principal', o corpo, halt e o label de fim."""
        main_name = context.MAIN().getText()
        self.emit("label", res=main_name)
        self.visit(context.block())
        self.emit("halt")
        self.emit("label", res=f"end_{main_name}")
        return None

    def visitFunctionDef(self, context: MOCPParser.FunctionDefContext):
        """
        Emite o label da função, vincula cada parâmetro formal ao seu
        valor de entrada (paramN → nome), visita o corpo e fecha com end_nome.
        """
        function_name = context.IDENTIFIER().getText()
        self.emit("label", res=function_name)

        if context.defParameters():
            params = context.defParameters()
            if not params.VOID():
                for i, param in enumerate(params.parameterDef()):
                    param_name = param.IDENTIFIER().getText()
                    self.emit("=", arg1=f"param{i + 1}", res=param_name)

        self.visit(context.block())
        self.emit("label", res=f"end_{function_name}")
        return None

    # ==========================================
    # 2. DECLARAÇÃO DE VARIÁVEIS
    # ==========================================

    def visitVariable(self, context: MOCPParser.VariableContext):
        """
        Trata todas as formas de declaração:
          - sem inicialização: nada a emitir (valor por omissão é 0)
          - com expressão: emite atribuição
          - com lers(): emite call lers (tamanho determinado em runtime)
          - com bloco de valores: delega em _emit_array_block
          - com tamanho fixo: emite alloc
        """
        variable_name = context.IDENTIFIER().getText()

        if context.ASSIGN():
            if context.expression():
                expr_val = context.expression().accept(self)
                self.emit("=", arg1=expr_val, res=variable_name)
            elif context.READS():
                temp = self.generate_new_temp()
                self.emit("call", arg1="lers", arg2="0", res=temp)
                self.emit("=", arg1=temp, res=variable_name)
            elif context.arrayBlock():
                self._emit_array_block(variable_name, context.arrayBlock())
        elif context.LBRACKET() and context.NUMBER():
            size = context.NUMBER().getText()
            self.emit("alloc", arg1=size, res=variable_name)

        return None

    def _emit_array_block(self, array_name, array_block_ctx):
        """
        Inicializa um vetor com lista de valores literais.
        O offset de cada elemento é calculado em tempo de compilação
        (inteiro: 4 bytes, real: 8 bytes).
        """
        if array_block_ctx.valueList():
            values = array_block_ctx.valueList().expression()
            symbol = self.symbol_table.resolve(array_name)
            width = 8 if symbol and symbol.get("type") == "real" else 4
            self.emit("alloc", arg1=str(len(values)), res=array_name)
            for i, expr in enumerate(values):
                val = self.visit(expr)
                offset_temp = self.generate_new_temp()
                self.emit("=", arg1=str(i * width), res=offset_temp)
                self.emit("[]=", arg1=offset_temp, arg2=val, res=array_name)

    # ==========================================
    # 3. EXPRESSÕES
    # ==========================================

    def visitPrimary(self, context: MOCPParser.PrimaryContext):
        """
        Trata os casos base: literais, identificadores, acessos indexados
        a vetores e chamadas de função.
        Para vetores, calcula o offset (índice × largura) antes de emitir [].
        """
        if context.IDENTIFIER() and context.LBRACKET():
            array_name = context.IDENTIFIER().getText()
            index_expr = context.expression().accept(self)
            symbol = self.symbol_table.resolve(array_name)
            width = 8 if symbol and symbol.get("type") == "real" else 4
            offset = self.generate_new_temp()
            self.emit("*", arg1=index_expr, arg2=str(width), res=offset)
            result = self.generate_new_temp()
            self.emit("[]", arg1=array_name, arg2=offset, res=result)
            return result
        elif context.IDENTIFIER():
            return context.IDENTIFIER().getText()
        elif context.LPAREN() and context.expression():
            return self.visit(context.expression())
        elif context.NUMBER():
            return context.NUMBER().getText()
        elif context.REAL_NUM():
            return context.REAL_NUM().getText()
        elif context.STRING_LITERAL():
            return context.STRING_LITERAL().getText()
        elif context.functionCall():
            return self.visit(context.functionCall())
        return None

    # Expressões binárias: visitam os dois operandos e emitem a operação.
    # Se tiver apenas um filho, delega para o nível de precedência abaixo.

    def visitExpressionAdd(self, context: MOCPParser.ExpressionAddContext):
        if context.getChildCount() == 1:
            return self.visit(context.getChild(0))
        left = self.visit(context.getChild(0))
        right = self.visit(context.getChild(2))
        op = context.getChild(1).getText() if context.getChild(1) else ""
        return self.emit(op, arg1=left, arg2=right)

    def visitExpressionMul(self, context: MOCPParser.ExpressionMulContext):
        if context.getChildCount() == 1:
            return self.visit(context.getChild(0))
        left = self.visit(context.getChild(0))
        right = self.visit(context.getChild(2))
        op = context.getChild(1).getText() if context.getChild(1) else ""
        return self.emit(op, arg1=left, arg2=right)

    def visitExpressionEquality(self, context: MOCPParser.ExpressionEqualityContext):
        if context.getChildCount() == 1:
            return self.visit(context.getChild(0))
        left = self.visit(context.getChild(0))
        right = self.visit(context.getChild(2))
        op = context.getChild(1).getText() if context.getChild(1) else ""
        return self.emit(op, arg1=left, arg2=right)

    def visitExpressionRelational(self, context: MOCPParser.ExpressionRelationalContext):
        if context.getChildCount() == 1:
            return self.visit(context.getChild(0))
        left = self.visit(context.getChild(0))
        right = self.visit(context.getChild(2))
        op = context.getChild(1).getText() if context.getChild(1) else ""
        return self.emit(op, arg1=left, arg2=right)

    def visitExpressionOr(self, context: MOCPParser.ExpressionOrContext):
        if context.getChildCount() == 1:
            return self.visit(context.getChild(0))
        left = self.visit(context.getChild(0))
        right = self.visit(context.getChild(2))
        return self.emit("||", arg1=left, arg2=right)

    def visitExpressionAnd(self, context: MOCPParser.ExpressionAndContext):
        if context.getChildCount() == 1:
            return self.visit(context.getChild(0))
        left = self.visit(context.getChild(0))
        right = self.visit(context.getChild(2))
        return self.emit("&&", arg1=left, arg2=right)

    def visitExpressionUnary(self, context: MOCPParser.ExpressionUnaryContext):
        """Negação aritmética (-) ou lógica (!), mapeadas para 'minus' e 'not'."""
        if context.getChildCount() == 1:
            return self.visit(context.getChild(0))
        op_text = context.getChild(0).getText() if context.getChild(0) else ""
        expr = self.visit(context.getChild(1))
        op = "minus" if op_text == "-" else "not"
        return self.emit(op, arg1=expr)

    def visitCastExpr(self, context: MOCPParser.CastExprContext):
        """Cast explícito (inteiro) ou (real), emitido como op 'cast'."""
        if context.getChildCount() == 1:
            return self.visit(context.getChild(0))
        cast_type = context.getChild(1).getText() if context.getChild(1) else ""
        expr = self.visit(context.getChild(3))
        return self.emit("cast", arg1=cast_type, arg2=expr)

    # ==========================================
    # 4. ATRIBUIÇÕES
    # ==========================================

    def visitAssignStatement(self, context: MOCPParser.AssignStatementContext):
        """
        Atribuição simples (x = expr) ou indexada (v[i] = expr).
        Para vetores, calcula o offset antes de emitir []=.
        """
        variable_name = context.IDENTIFIER().getText()

        if context.LBRACKET() is None:
            expr_val = self.visit(context.expression(0))
            self.emit("=", arg1=expr_val, res=variable_name)
        else:
            index = self.visit(context.expression(0))
            value = self.visit(context.expression(1))
            symbol = self.symbol_table.resolve(variable_name)
            width = 8 if symbol and symbol.get("type") == "real" else 4
            offset = self.generate_new_temp()
            self.emit("*", arg1=index, arg2=str(width), res=offset)
            self.emit("[]=", arg1=offset, arg2=value, res=variable_name)

        return None

    def visitExpressionOrAssign(self, context: MOCPParser.ExpressionOrAssignContext):
        """
        Usado nas partes de inicialização e atualização do ciclo 'para'.
        Pode ser uma atribuição (i = 0) ou uma expressão pura.
        """
        if context.ASSIGN():
            variable_name = context.IDENTIFIER().getText()
            if context.LBRACKET() is None:
                expr_val = self.visit(context.expression(0))
                self.emit("=", arg1=expr_val, res=variable_name)
            else:
                index = self.visit(context.expression(0))
                value = self.visit(context.expression(1))
                symbol = self.symbol_table.resolve(variable_name)
                width = 8 if symbol and symbol.get("type") == "real" else 4
                offset = self.generate_new_temp()
                self.emit("*", arg1=index, arg2=str(width), res=offset)
                self.emit("[]=", arg1=offset, arg2=value, res=variable_name)
            return None
        return self.visit(context.expression(0))

    # ==========================================
    # 5. CHAMADAS DE FUNÇÃO
    # ==========================================

    def visitFunctionCall(self, context: MOCPParser.FunctionCallContext):
        """
        Emite um 'param' por cada argumento (da esquerda para a direita),
        seguido de 'call nome, nargs'. Funções built-in (ler, lerc, lers)
        não têm argumentos explícitos.
        """
        if context.IDENTIFIER():
            function_name = context.IDENTIFIER().getText()
            args = []
            if context.arguments():
                for expr in context.arguments().expression():
                    args.append(self.visit(expr))
        elif context.READ():
            function_name, args = "ler", []
        elif context.READC():
            function_name, args = "lerc", []
        elif context.READS():
            function_name, args = "lers", []
        else:
            return None

        for arg in args:
            self.emit("param", arg1=arg)

        result = self.generate_new_temp()
        self.emit("call", arg1=function_name, arg2=str(len(args)), res=result)
        return result

    # ==========================================
    # 6. CONTROLO DE FLUXO E CICLOS
    # ==========================================

    def visitStatement(self, context: MOCPParser.StatementContext):
        """
        Condicional se/senao: emite ifFalse para saltar o bloco 'then'.
        Com 'senao', acrescenta um goto antes do bloco 'else' para que
        o bloco 'then' não caia no 'else' após terminar.
        """
        if context.IF():
            condition = self.visit(context.expression())
            label_false = self.generate_new_label()
            label_end   = self.generate_new_label()

            self.emit("ifFalse", arg1=condition, res=label_false)
            self.visit(context.block(0))

            if context.ELSE():
                self.emit("goto", res=label_end)
                self.emit("label", res=label_false)
                self.visit(context.block(1))
                self.emit("label", res=label_end)
            else:
                self.emit("label", res=label_false)

            return None

        return self.visitChildren(context)

    def visitWhileStatement(self, context: MOCPParser.WhileStatementContext):
        """
        Ciclo enquanto: label de início → avalia condição → ifFalse sai
        → corpo → goto início → label de saída.
        """
        label_begin = self.generate_new_label()
        label_end   = self.generate_new_label()

        self.emit("label",   res=label_begin)
        condition = self.visit(context.expression())
        self.emit("ifFalse", arg1=condition, res=label_end)
        self.visit(context.block())
        self.emit("goto",    res=label_begin)
        self.emit("label",   res=label_end)
        return None

    def visitForStatement(self, context: MOCPParser.ForStatementContext):
        """
        Ciclo para: inicialização → label início → condição → corpo
        → atualização → goto início → label saída.
        Os três campos são identificados percorrendo os filhos do nó
        e distinguindo pelos tipos e pela posição dos ';'.
        """
        initializer_node = None
        condition_node   = None
        update_node      = None
        passed_first_semi = False

        for i in range(context.getChildCount()):
            child = context.getChild(i)
            if child is not None and child.getText() == ";":
                passed_first_semi = True
            elif isinstance(child, MOCPParser.ExpressionOrAssignContext):
                if not passed_first_semi:
                    initializer_node = child
                else:
                    update_node = child
            elif isinstance(child, MOCPParser.ExpressionContext):
                condition_node = child

        if initializer_node:
            self.visit(initializer_node)

        label_begin = self.generate_new_label()
        label_end   = self.generate_new_label()

        self.emit("label", res=label_begin)
        if condition_node:
            condition = self.visit(condition_node)
            self.emit("ifFalse", arg1=condition, res=label_end)

        self.visit(context.block())

        if update_node:
            self.visit(update_node)

        self.emit("goto",  res=label_begin)
        self.emit("label", res=label_end)
        return None

    # ==========================================
    # 7. ENTRADA / SAÍDA
    # ==========================================

    def visitWriteStatement(self, context: MOCPParser.WriteStatementContext):
        """
        Mapeia cada função de escrita para a instrução TAC correspondente.
        Para escreverv(), usa _extract_identifier para obter o nome do vetor
        diretamente, sem criar temporários (a semântica já validou o argumento).
        """
        if context.WRITE():
            self.emit("write",  arg1=self.visit(context.expression()))
        elif context.WRITEC():
            self.emit("writec", arg1=self.visit(context.expression()))
        elif context.WRITEV():
            array_name = self._extract_identifier(context.expression())
            if array_name is None:
                array_name = self.visit(context.expression())
            self.emit("writev", arg1=array_name)
        elif context.WRITES():
            self.emit("writes", arg1=context.stringArgument().getText())
        return None

    # ==========================================
    # 8. RETORNO
    # ==========================================

    def visitReturnStatement(self, context: MOCPParser.ReturnStatementContext):
        """Emite 'return valor' ou 'return' consoante a função retorne ou não um valor."""
        if context.expression():
            self.emit("return", arg1=self.visit(context.expression()))
        else:
            self.emit("return")
        return None
