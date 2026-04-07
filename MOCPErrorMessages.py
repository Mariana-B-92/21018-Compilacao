class MOCPErrorMessages:
    MISSING_MAIN = "O protótipo da função 'principal' está em falta."
    ARRAY_INVALID_INDEX = "O índice do vetor tem de ser um número inteiro."
    MOD_ONLY_FOR_INTEGERS = "O operador módulo (%) exige operandos do tipo 'inteiro'."
    INVALID_RELATIONAL_OPERATORS = "Os operadores relacionais exigem operandos numéricos."
    IF_CONDITION_NOT_NUMERICAL = "A condição da instrução 'se' tem de resultar num valor numérico."
    WHILE_CONDITION_NOT_NUMERICAL = "A condição do ciclo 'enquanto' tem de resultar num valor numérico."
    FOR_CONDITION_NOT_NUMERICAL = "A condição do ciclo 'para' tem de resultar num valor numérico."
    WRITEC_INVALID_TYPE = "A função 'escreverc' exige uma expressão do tipo 'inteiro' (código ASCII)."
    WRITES_INVALID_TYPE = "A instrução 'escrevers' com variável exige um vetor de carateres."
    RETURN_TYPE_VOID = "Uma função do tipo 'vazio' não deve retornar um valor."
    RETURN_TYPE_INVALID = "Não é possível retornar um valor 'real' numa função declarada como 'inteiro'."
    UNIDENTIFIED_PARAMETERS = "Os parâmetros na definição da função têm de ter um identificador."

    @staticmethod
    def prototype_already_declared(function_name):
        return f"O protótipo da função '{function_name}' já foi declarado."

    @staticmethod
    def prototype_not_declared(function_name):
        return f"A função '{function_name}' não possui protótipo declarado previamente."

    @staticmethod
    def variable_already_declared(variable_name):
        return f"A variável '{variable_name}' já foi declarada neste escopo."

    @staticmethod
    def parameter_already_declared(parameter_name):
        return f"O parâmetro '{parameter_name}' já foi declarado neste escopo."

    @staticmethod
    def variable_not_declared(variable_name):
        return f"A variável '{variable_name}' não foi declarada antes da sua utilização."

    @staticmethod
    def variable_is_a_function(variable_name):
        return f"'{variable_name}' é uma função e não pode ser usada como variável."

    @staticmethod
    def variable_not_a_function(variable_name):
        return f"'{variable_name}' não é uma função."

    @staticmethod
    def array_not_declared(array_name):
        return f"O vetor '{array_name}' não foi declarado antes da sua utilização."

    @staticmethod
    def variable_is_not_vector(variable_name):
        return f"A variável '{variable_name}' não é um vetor para ser indexada."

    @staticmethod
    def invalid_operation(left_type, right_type):
        return f"Operação aritmética inválida entre tipos '{left_type}' e '{right_type}'."

    @staticmethod
    def variable_wrong_type(variable_name):
        return f"Não é possível atribuir um 'real' à variável '{variable_name}' do tipo 'inteiro'."

    @staticmethod
    def function_not_declared(function_name):
        return f"A função '{function_name}' não foi declarada antes da sua chamada."

    @staticmethod
    def invalid_operation_for_type(expression_type):
        return f"Negação aritmética inválida para o tipo '{expression_type}'."

    @staticmethod
    def write_c_not_vector(variable_name):
        return f"A instrução 'escreverv' exige um vetor. '{variable_name}' é uma variável escalar."

    @staticmethod
    def unexpected_return_type(function_type):
        return f"A função esperava um retorno do tipo '{function_type}'."

    @staticmethod
    def required_index(variable_name):
        return f"A variável '{variable_name}' é um vetor e requer um índice para atribuição."
