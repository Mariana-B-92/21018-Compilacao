grammar MOCP;

/* =========================
 * LEXER
 * =========================
 */

/* PALAVRAS-CHAVE DA LINGUAGEM */
INTEIRO   : 'inteiro' ;
REAL      : 'real' ;
VAZIO     : 'vazio' ;

PRINCIPAL : 'principal' ;

/* FUNÇÕES DE LEITURA */
LER  : 'ler' ;
LERC : 'lerc' ;
LERS : 'lers' ;

/* FUNÇÕES DE ESCRITA */
ESCREVER  : 'escrever' ;
ESCREVERC : 'escreverc' ;
ESCREVERV : 'escreverv' ;
ESCREVERS : 'escrevers' ;

/* ESTRUTURAS DE CONTROLO */
SE       : 'se' ;
SENAO    : 'senao' ;
ENQUANTO : 'enquanto' ;
PARA     : 'para' ;
RETORNAR : 'retornar' ;

/* PALAVRAS RESERVADAS DE C NÃO PERMITIDAS EM MOCP */
ERRO_PALAVRA_C
    : 'int' | 'double' | 'void' | 'main'
    | 'if' | 'else' | 'while' | 'for' | 'return'
    | 'char' | 'float' | 'long' | 'short' | 'unsigned' | 'signed'
    | 'struct' | 'union' | 'enum' | 'typedef' | 'sizeof'
    | 'break' | 'continue' | 'switch' | 'case' | 'default' | 'do'
    | 'printf' | 'scanf' | 'fprintf' | 'fscanf'
    | 'malloc' | 'free' | 'NULL' | 'null'
    | 'include' | 'define'
    { throw new RuntimeException("Uso de palavra reservada de C não permitido: " + getText()); }
    ;

/* OPERADORES DE C NÃO PERMITIDOS EM MOCP */
ERRO_OPERADORES_C
    : '++' | '--'
    | '+=' | '-=' | '*=' | '/=' | '%='
    | '&=' | '|=' | '^=' | '<<=' | '>>='
    | '<<' | '>>'
    | '->'  | '.'
    { throw new RuntimeException("Operador não permitido em MOCP: " + getText()); }
    ;

/* OPERADORES ARITMÉTICOS */
MAIS   : '+' ;
MENOS  : '-' ;
MULT   : '*' ;
DIV    : '/' ;
MODULO : '%' ;

/* OPERADORES RELACIONAIS */
MENOR       : '<' ;
MENORIGUAL  : '<=' ;
MAIOR       : '>' ;
MAIORIGUAL  : '>=' ;
IGUAL       : '==' ;
DIFERENTE   : '!=' ;

/* OPERADORES LÓGICOS */
E_LOGICO  : '&&' ;
OU_LOGICO : '||' ;
NAO       : '!' ;

/* PONTUAÇÃO */
ATRIBUICAO : '=' ;
VIRGULA    : ',' ;
PONTOVIRG  : ';' ;

/* DELIMITADORES */
ABRECOLCH   : '[' ;
FECHACOLCH  : ']' ;
ABRECHAVES  : '{' ;
FECHACHAVES : '}' ;
ABREPAR     : '(' ;
FECHAPAR    : ')' ;

/* LITERAIS */
STRINGLITERAL : '"' (ESC_SEQ | ~["\\\r\n])* '"' ;
fragment ESC_SEQ : '\\' [\\'"nrt0] ; /* sequências de escape suportadas */

NUM_REAL : [0-9]+ '.' [0-9]+ ;
NUMERO   : [0-9]+ ;

/* IDENTIFICADORES */
IDENTIFICADOR : [a-zA-Z_][a-zA-Z0-9_]* ;

/* ELEMENTOS IGNORADOS */
COMENTARIO_BLOCK : '/*' .*? '*/' -> skip ;
COMENTARIO_LINE  : '//' ~[\r\n]*  -> skip ;
ESPACO           : [ \t\r\n]+     -> skip ;


/* =========================
 * PARSER
 * =========================
 */

/* estrutura global do programa */
programa
    : prototipos funcoes funcaoPrincipal EOF
    ;

/* protótipos devem aparecer antes das funções */
prototipos
    : prototipo*
    ;

prototipo
    : tipoFunc IDENTIFICADOR ABREPAR parametrosProto? FECHAPAR PONTOVIRG
    ;

parametrosProto
    : parametroProto (VIRGULA parametroProto)*
    ;

/* parâmetros sem nome (protótipos) */
parametroProto
    : tipoVar (ABRECOLCH FECHACOLCH)?
    ;

/* definição de funções */
funcoes
    : funcao*
    ;

funcao
    : tipoFunc IDENTIFICADOR ABREPAR parametros? FECHAPAR bloco
    ;

parametros
    : parametro (VIRGULA parametro)*
    ;

/* parâmetros com nome */
parametro
    : tipoVar IDENTIFICADOR (ABRECOLCH FECHACOLCH)?
    ;

/* função principal obrigatória */
funcaoPrincipal
    : VAZIO PRINCIPAL ABREPAR VAZIO FECHAPAR bloco
    ;

/* declaração de variáveis (simples ou vetores) */
declaracao
    : tipoVar listaVariaveis PONTOVIRG
    ;

listaVariaveis
    : variavel (VIRGULA variavel)*
    ;

/* variável:
 * - simples
 * - vetor com tamanho
 * - vetor com tamanho inferido por inicialização
 */
variavel
    : IDENTIFICADOR
      ( ABRECOLCH NUMERO   FECHACOLCH inicializacao?
      | ABRECOLCH          FECHACOLCH inicializacao
      | inicializacao
      )?
    ;

/* inicialização com expressão, array ou leitura */
inicializacao
    : ATRIBUICAO (expressao | blocoArray | chamadaLeitura)
    ;

/* inicialização de vetores com lista de valores */
blocoArray
    : ABRECHAVES listaValores? FECHACHAVES
    ;

listaValores
    : expressao (VIRGULA expressao)*
    ;

/* expressão aritmética com precedência */
expressao
    : expressaoAdd
    ;

/* operadores + e - */
expressaoAdd
    : expressaoMul ((MAIS | MENOS) expressaoMul)*
    ;

/* operadores *, / e % */
expressaoMul
    : expressaoUnaria ((MULT | DIV | MODULO) expressaoUnaria)*
    ;

/* operadores unários: ! e - */
expressaoUnaria
    : NAO   expressaoUnaria
    | MENOS expressaoUnaria
    | castExpr
    ;

/* casting explícito (inteiro/real) */
castExpr
    : (ABREPAR (INTEIRO | REAL) FECHAPAR)* primary
    ;

/* condições simplificadas conforme especificação */
condicao
    : condicaoOr
    ;

condicaoOr
    : condicaoAnd (OU_LOGICO condicaoAnd)*
    ;

condicaoAnd
    : condicaoNot (E_LOGICO condicaoNot)*
    ;

condicaoNot
    : NAO condicaoNot
    | condicaoBase
    ;

/* formas permitidas:
 * - (condição)
 * - expr op expr
 * - expr
 */
condicaoBase
    : ABREPAR condicao FECHAPAR
    | expressao opRelacional expressao
    | expressao
    ;

opRelacional
    : MENOR | MENORIGUAL | MAIOR | MAIORIGUAL | IGUAL | DIFERENTE
    ;

primary
    : ABREPAR expressao FECHAPAR
    | chamadaLeitura
    | NUM_REAL
    | NUMERO
    | chamadaFuncao
    | acessoArray
    | IDENTIFICADOR
    ;

/* chamada de função */
chamadaFuncao
    : IDENTIFICADOR ABREPAR argumentos? FECHAPAR
    ;

/* acesso a posição de vetor */
acessoArray
    : IDENTIFICADOR ABRECOLCH expressao FECHACOLCH
    ;

argumentos
    : expressao (VIRGULA expressao)*
    ;

/* leitura de valores */
chamadaLeitura
    : LER  ABREPAR FECHAPAR
    | LERC ABREPAR FECHAPAR
    | LERS ABREPAR FECHAPAR
    ;

/* bloco de instruções */
bloco
    : ABRECHAVES instrucoes FECHACHAVES
    ;

instrucoes
    : instrucao*
    ;

instrucao
    : instrucaoSe
    | instrucaoEnquanto
    | instrucaoPara
    | instrucaoEscrita
    | instrucaoRetornar
    | instrucaoAtribuicao
    | declaracao
    | bloco
    | instrucaoExpressao
    ;

/* expressão usada como instrução */
instrucaoExpressao
    : expressao PONTOVIRG
    ;

/* estrutura condicional (else opcional) */
instrucaoSe
    : SE ABREPAR condicao FECHAPAR bloco (SENAO bloco)?
    ;

/* ciclo enquanto */
instrucaoEnquanto
    : ENQUANTO ABREPAR condicao FECHAPAR bloco
    ;

/* ciclo para com sintaxe simplificada */
instrucaoPara
    : PARA ABREPAR
        inicializacaoPara? PONTOVIRG
        condicao           PONTOVIRG
        incrementoPara?
      FECHAPAR bloco
    ;

inicializacaoPara
    : IDENTIFICADOR ATRIBUICAO expressao
    ;

incrementoPara
    : IDENTIFICADOR ATRIBUICAO expressao
    ;

/* instruções de escrita */
instrucaoEscrita
    : ESCREVER  ABREPAR expressao      FECHAPAR PONTOVIRG
    | ESCREVERC ABREPAR expressao      FECHAPAR PONTOVIRG
    | ESCREVERV ABREPAR IDENTIFICADOR  FECHAPAR PONTOVIRG
    | ESCREVERS ABREPAR argumentoString FECHAPAR PONTOVIRG
    ;

instrucaoRetornar
    : RETORNAR expressao? PONTOVIRG
    ;

/* atribuição a variável ou posição de vetor */
instrucaoAtribuicao
    : alvo ATRIBUICAO expressao PONTOVIRG
    ;

alvo
    : IDENTIFICADOR
    | IDENTIFICADOR ABRECOLCH expressao FECHACOLCH
    ;

/* argumento pode ser variável (vetor) ou string literal */
argumentoString
    : IDENTIFICADOR
    | STRINGLITERAL
    ;

/* tipos disponíveis */
tipoVar  : INTEIRO | REAL ;
tipoFunc : INTEIRO | REAL | VAZIO ;

