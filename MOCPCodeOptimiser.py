class MOCPCodeOptimiser:
    def __init__(self, code):
        self.code = code

    def optimize(self):
        """Aplica uma série de passagens de otimização ao código intermédio."""

        optimised = self.code

        for _ in range(3):
            # Desdobramento de Constantes
            optimised = self.constant_folding(optimised)

            # Simplificação Algébrica
            optimised = self.algebraic_simplification(optimised)

            # Propagação de Cópia
            optimised = self.copy_propagation(optimised)

            # Eliminação de Código Morto
            optimised = self.dead_code_elimination(optimised)

        return optimised

    def constant_folding(self, code):
        new_code = []

        for instruction in code:
            parts = instruction.split(' ')

            if len(parts) == 5:
                result, assign, arg1, operator, arg2 = parts

                if assign == '=':
                    if self.is_number(arg1) and self.is_number(arg2):
                        val1 = float(arg1) if '.' in arg1 else int(arg1)
                        val2 = float(arg2) if '.' in arg2 else int(arg2)
                        res_val = None

                        try:
                            if operator == '+':
                                res_val = val1 + val2
                            elif operator == '-':
                                res_val = val1 - val2
                            elif operator == '*':
                                res_val = val1 * val2
                            elif operator == '/':
                                res_val = val1 / val2
                            elif operator == '%':
                                res_val = val1 % val2
                        except ZeroDivisionError:
                            pass

                        if res_val is not None:
                            if isinstance(res_val, float) and res_val.is_integer():
                                res_val = int(res_val)

                            new_code.append(f"{result} = {res_val}")
                            continue

            new_code.append(instruction)
        return new_code

    @staticmethod
    def algebraic_simplification(code):
        new_code = []

        for instruction in code:
            parts = instruction.split(' ')

            if len(parts) == 5:
                result, assign, arg1, operator, arg2 = parts

                if assign == '=':
                    if operator in ('+', '-') and arg2 == '0':
                        new_code.append(f"{result} = {arg1}")
                        continue
                    elif operator == '+' and arg1 == '0':
                        new_code.append(f"{result} = {arg2}")
                        continue
                    elif operator in ('*', '/') and arg2 == '1':
                        new_code.append(f"{result} = {arg1}")
                        continue
                    elif operator == '*' and arg1 == '1':
                        new_code.append(f"{result} = {arg2}")
                        continue
                    elif operator == '*' and (arg1 == '0' or arg2 == '0'):
                        new_code.append(f"{result} = 0")
                        continue

            new_code.append(instruction)
        return new_code

    @staticmethod
    def copy_propagation(code):
        new_code = []
        copies = {}

        for instruction in code:
            # Regra dos Blocos Básicos: invalida propagação ao encontrar desvios ou rótulos
            if instruction.endswith(':') or instruction.startswith('goto') or instruction.startswith('ifFalse'):
                copies.clear()
                new_code.append(instruction)
                continue

            parts = instruction.split(' ')

            if len(parts) == 3:
                dest, assign, src = parts

                if assign == '=':
                    if src in copies:
                        src = copies.get(src)

                    copies[dest] = src
                    new_code.append(f"{dest} = {src}")
                    continue

            if len(parts) == 5:
                result, assign, arg1, operator, arg2 = parts

                if assign == '=':
                    if arg1 in copies: arg1 = copies.get(arg1)
                    if arg2 in copies: arg2 = copies.get(arg2)

                    keys_to_remove = [k for k, v in copies.items() if v == result or k == result]
                    for key in keys_to_remove: del copies[key]

                    new_code.append(f"{result} = {arg1} {operator} {arg2}")
                    continue

            new_instruction = []

            for part in parts:
                if part in copies:
                    new_instruction.append(copies.get(part))
                else:
                    new_instruction.append(part)

            if len(parts) > 2 and parts[1] == '=':
                dest = parts[0]
                variable_name = dest.split('[')[0] if '[' in dest else dest
                keys_to_remove = [k for k, v in copies.items() if v == variable_name or k == variable_name]
                for key in keys_to_remove: del copies[key]

            new_code.append(" ".join(new_instruction))

        return new_code

    def dead_code_elimination(self, code):
        new_code = []
        used_vars = set()

        for instruction in reversed(code):
            clean_instruction = instruction.replace('[', ' ').replace(']', ' ')
            tokens = clean_instruction.split()

            parts = instruction.split(' ')

            if len(parts) >= 3 and '=' in parts and parts.index('=') == 1:
                dest = parts[0]

                # Elimina o temporário apenas se ele não for usado e NÃO for um array (v[t1])
                if dest.startswith('t') and dest.replace('t','').isdigit() and dest not in used_vars:
                    if '[' not in dest:
                        continue

                # Marca o lado direito como usado
                for token in tokens[2:]:
                    if token.isalnum() and not self.is_number(token):
                        used_vars.add(token)

                # Se for atribuição a vetor, o índice e o nome contam como usados
                if '[' in dest:
                    array_parts = dest.split('[')
                    array_name = array_parts[0]
                    index = array_parts[1].replace(']', '')

                    if array_name.isalnum() and not self.is_number(array_name):
                        used_vars.add(array_name)

                    if index.isalnum() and not self.is_number(index):
                        used_vars.add(index)

                new_code.append(instruction)
            else:
                for token in tokens:
                    if token.isalnum() and not token.startswith('L') and not self.is_number(token) and token not in (
                    'goto', 'ifFalse', 'param', 'call', 'return'):
                        used_vars.add(token)
                new_code.append(instruction)

        return list(reversed(new_code))

    # ==========================================
    # FUNÇÕES AUXILIARES PARA TIPOS
    # ==========================================

    @staticmethod
    def is_number(text):
        """Função auxiliar para verificar se uma string é um número (inteiro ou real)."""

        try:
            float(text)
            return True
        except ValueError:
            return False
