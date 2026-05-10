class MOCPErrorMessages:
    ARRAY_INVALID_INDEX = "O índice do vetor tem de ser um número inteiro."
    CAST_ALLOWED = "Cast só pode ser para 'inteiro' ou 'real'."
    CAST_EXPRESSIONS = "Cast só pode ser aplicado a expressões numéricas."
    DECLARED_MAIN = "A função 'principal' já foi definida anteriormente."
    FOR_CONDITION_NOT_NUMERICAL = "A condição do ciclo 'para' tem de resultar num valor numérico."
    FOR_INVALID_ASSIGNMENT = "Expressão de atribuição inválida no ciclo 'para'."
    IF_CONDITION_NOT_NUMERICAL = "A condição da instrução 'se' tem de resultar num valor numérico."
    INVALID_RELATIONAL_OPERATORS = "Os operadores relacionais exigem operandos numéricos."
    MISSING_MAIN = "O protótipo da função 'principal' está em falta."
    MOD_ONLY_FOR_INTEGERS = "O operador módulo (%) exige operandos do tipo 'inteiro'."
    READS_INVALID_TYPE = "Variável inicializada com 'lers()' tem de ser do tipo 'inteiro[]'."
    RETURN_TYPE_INVALID = "Não é possível retornar um valor 'real' numa função declarada como 'inteiro'."
    RETURN_TYPE_VOID = "Uma função do tipo 'vazio' não deve retornar um valor."
    UNIDENTIFIED_PARAMETERS = "Os parâmetros na definição da função têm de ter um identificador."
    WHILE_CONDITION_NOT_NUMERICAL = "A condição do ciclo 'enquanto' tem de resultar num valor numérico."
    WRITE_INVALID_TYPE = "Função 'escrever()' não aceita strings. Use 'escrevers()'."
    WRITEC_INVALID_TYPE = "A função 'escreverc' exige uma expressão do tipo 'inteiro' (código ASCII)."
    WRITES_INVALID_TYPE = "A instrução 'escrevers' com variável exige um vetor de carateres."

    # ==========================================
    # 1. FUNÇÕES E PARÂMETROS
    # ==========================================

    @staticmethod
    def function_already_declared(function_name):
        return f"A função '{function_name}' já foi definida anteriormente."

    @staticmethod
    def function_arg_not_vector(argument, function_name):
        return f"Argumento {argument} da função '{function_name}' deve ser um vetor."

    @staticmethod
    def function_arg_wrong_type(argument, function_name, argument_type, expected_type):
        return f"Argumento {argument} da função '{function_name}' é do tipo '{argument_type}', mas esperava '{expected_type}'."

    @staticmethod
    def function_not_declared(function_name):
        return f"A função '{function_name}' não foi declarada antes da sua chamada."

    @staticmethod
    def function_wrong_num_arguments(function_name, expected_params, received_params):
        return f"Função '{function_name}' espera {expected_params} argumento(s), mas recebeu {received_params}."

    @staticmethod
    def parameter_already_declared(parameter_name):
        return f"O parâmetro '{parameter_name}' já foi declarado neste escopo."

    @staticmethod
    def unexpected_return_type(function_type):
        return f"A função esperava um retorno do tipo '{function_type}'."

    # ==========================================
    # 2. PROTÓTIPOS
    # ==========================================

    @staticmethod
    def prototype_already_declared(function_name):
        return f"O protótipo da função '{function_name}' já foi declarado."

    @staticmethod
    def prototype_not_declared(function_name):
        return f"A função '{function_name}' não possui protótipo declarado previamente."

    # ==========================================
    # 3. VARIÁVEIS
    # ==========================================

    @staticmethod
    def variable_already_declared(variable_name):
        return f"A variável '{variable_name}' já foi declarada neste escopo."

    @staticmethod
    def variable_is_a_function(variable_name):
        return f"'{variable_name}' é uma função e não pode ser usada como variável."

    @staticmethod
    def variable_not_a_function(variable_name):
        return f"'{variable_name}' não é uma função."

    @staticmethod
    def variable_not_a_vector(variable_name):
        return f"A variável '{variable_name}' não é um vetor para ser indexada."

    @staticmethod
    def variable_not_declared(variable_name):
        return f"A variável '{variable_name}' não foi declarada antes da sua utilização."

    @staticmethod
    def variable_wrong_type(variable_name):
        return f"Não é possível atribuir um 'real' à variável '{variable_name}' do tipo 'inteiro'."

    # ==========================================
    # 4. VETORES
    # ==========================================

    @staticmethod
    def vector_not_declared(array_name):
        return f"O vetor '{array_name}' não foi declarado antes da sua utilização."

    @staticmethod
    def vector_required_index(variable_name):
        return f"A variável '{variable_name}' é um vetor e requer um índice para atribuição."

    @staticmethod
    def vector_wrong_element_type(base_type, expression_type):
        return f"Elemento do vetor de tipo incompatível (esperado '{base_type}', recebido '{expression_type}')."

    @staticmethod
    def vector_wrong_size(variable_name, declared_size, num_elements):
        return f"Vetor '{variable_name}' declarado com tamanho {declared_size} mas inicializado com {num_elements} elementos."

    @staticmethod
    def write_c_not_vector(variable_name):
        return f"A instrução 'escreverv' exige um vetor. '{variable_name}' é uma variável escalar."

    # ==========================================
    # 5. OPERAÇÕES
    # ==========================================

    @staticmethod
    def invalid_operation(left_type, right_type):
        return f"Operação aritmética inválida entre tipos '{left_type}' e '{right_type}'."

    @staticmethod
    def invalid_operation_for_type(expression_type):
        return f"Negação aritmética inválida para o tipo '{expression_type}'."
