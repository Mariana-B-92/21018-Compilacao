grammar MOCP;

/*
 * -----------
 * LEXER RULES
 * -----------
 */

// Tipos de dados suportados:
INT     :   'inteiro'   ;   // Tipo inteiro.
FLOAT   :   'real'      ;   // Tipo real.
VOID    :   'vazio'     ;   // Ausência de valor.

// Função de entrada do programa:
MAIN    :   'principal' ;

// Estruturas de controlo:
IF      :   'se'        ;   // Condicional.
ELSE    :   'senao'     ;   // Alternativa.
WHILE   :   'enquanto'  ;   // Ciclo while.
FOR     :   'para'      ;   // Ciclo for.
RETURN  :   'retornar'  ;   // Retorno de função.

// Funções de leitura (input):
READ    :   'ler'   ;   // Leitura numérica.
READC   :   'lerc'  ;   // Leitura de caráter (ASCII).
READS   :   'lers'  ;   // Leitura de string como vetor de inteiros (ASCII, terminada em 0).

// Funções de escrita (output):
WRITE   : 'escrever'  ;   // Escrita numérica.
WRITEC  : 'escreverc' ;   // Escrita de caráter.
WRITEV  : 'escreverv' ;   // Escrita de vetor.
WRITES  : 'escrevers' ;   // Escrita de string.

// Operadores aritméticos suportados (subconjunto de C):
PLUS    : '+' ;
MINUS   : '-' ;
MULT    : '*' ;
DIV     : '/' ;
MOD     : '%' ;

// Operadores relacionais:
LT      : '<'   ;
LE      : '<='  ;
GT      : '>'   ;
GE      : '>='  ;
EQ      : '=='  ;
NEQ     : '!='  ;

// Operadores lógicos:
AND     :   '&&'    ;
OR      :   '||'    ;
NOT     :   '!'     ;

// Símbolos e pontuação:
ASSIGN      : '=' ;
COMMA       : ',' ;
SEMI_COLON  : ';' ;
LBRACKET    : '[' ;
RBRACKET    : ']' ;
LBRACE      : '{' ;
RBRACE      : '}' ;
LPAREN      : '(' ;
RPAREN      : ')' ;

// Literais e identificadores:
STRING_LITERAL  : '"' ( '\\' . | ~["\\\r\n] )* '"'  ;   // String literal com escapes.
REAL_NUM        : [0-9]+ '.' [0-9]+                 ;   // Literal real.
NUMBER          : [0-9]+                            ;   // Literal inteiro.
IDENTIFIER      : [a-zA-Z_][a-zA-Z0-9_]*            ;   // Identificador válido.

// Elementos ignorados:
BLOCK_COMMENT : '/*' .*? '*/' -> skip ;     // Comentário multi-linha.
LINE_COMMENT  : '//' ~[\r\n]* -> skip ;     // Comentário de linha.
WS            : [ \t\r\n]+ -> skip    ;     // Espaço.

/*
 * -----------
 * PARSER
 * -----------
 */

/* ---------- Programa ---------- */

/* Estrutura global: protótipos seguidos do corpo executável. */
program
    : prototypes body EOF
    ;

/* Conjunto de protótipos opcionais seguido obrigatoriamente do protótipo da função principal. */
prototypes
    : prototype* mainPrototype
    ;

/* Sequência de unidades (declarações ou funções) terminando obrigatoriamente na implementação da função principal. */
body
    : unit* mainFunction
    ;

/* Elemento de topo do corpo: pode ser uma função definida ou uma declaração global. */
unit
    : functionDef
    | declaration
    ;

/* ---------- Funções ---------- */

/* Assinatura de função sem corpo. */
prototype
    : returnType IDENTIFIER LPAREN parameters? RPAREN SEMI_COLON
    ;

/* Declaração obrigatória da função principal. */
mainPrototype
    : VOID MAIN LPAREN VOID? RPAREN SEMI_COLON
    ;

/* Implementação da função principal. */
mainFunction
    : VOID MAIN LPAREN VOID? RPAREN block
    ;

/* Definição de função com corpo. */
functionDef
    : returnType IDENTIFIER LPAREN parameters? RPAREN block
    ;

/* Parâmetros formais: podem ser omitidos, explicitamente 'vazio', ou uma lista tipada de parâmetros. */
parameters
    : VOID
    | parameter (COMMA parameter)*
    ;

/* Parâmetro simples ou vetor. */
parameter
    : type IDENTIFIER?
    | type IDENTIFIER? LBRACKET RBRACKET
    ;

/* Tipos suportados pela linguagem. */
type
    : INT
    | FLOAT
    ;

returnType
    : INT
    | FLOAT
    | VOID
    ;

/* ---------- Declarações ---------- */

/* Declaração de variáveis, com ou sem inicialização. */
declaration
    : type variableList SEMI_COLON
    ;

/* Conjunto de variáveis declaradas no mesmo contexto. */
variableList
    : variable (COMMA variable)*
    ;

/* Declaração de variável:
 * - escalar simples (com ou sem inicialização)
 * - vetor com tamanho fixo
 * - vetor com inferência via inicialização (lista ou leitura com lers)
 * Nota: lers() tem alternativa explícita pois infere o tamanho do vetor;
 * ler() e lerc() são tratados como expressões normais via chamadaFuncao.
 */
variable
    : IDENTIFIER
    | IDENTIFIER ASSIGN expression
    | IDENTIFIER LBRACKET NUMBER RBRACKET
    | IDENTIFIER LBRACKET RBRACKET ASSIGN READS LPAREN RPAREN
    | IDENTIFIER LBRACKET RBRACKET ASSIGN arrayBlock
    | IDENTIFIER LBRACKET NUMBER RBRACKET ASSIGN arrayBlock
    ;

/* Inicialização de vetor através de lista de expressões entre chavetas. */
arrayBlock
    : LBRACE valueList? RBRACE
    ;

/* Valores usados na inicialização de vetores. */
valueList
    : expression (COMMA expression)*
    ;

/* ---------- Expressões ---------- */

/* Ponto de entrada da hierarquia de precedência das expressões. */
expression
    : expressionOr
    ;

/* Operador lógico OU (menor precedência). */
expressionOr
    : expressionOr OR expressionOr
    | expressionAnd
    ;

/* Operador lógico E. */
expressionAnd
    : expressionAnd AND expressionEquality
    | expressionEquality
    ;

/* Expressões com operadores de igualdade (==, !=), associativas à esquerda. */
expressionEquality
    : expressionRelational
    | expressionEquality equalityOp expressionRelational
    ;

/* Operadores de igualdade. */
equalityOp
    : EQ
    | NEQ
    ;

/* Expressões com operadores relacionais (<, <=, >, >=). */
expressionRelational
    : expressionAdd
    | expressionRelational relationalOp expressionAdd
    ;

/* Operadores relacionais (<, <=, >, >=). */
relationalOp
    : LT
    | LE
    | GT
    | GE
    ;

/* Soma e subtração. */
expressionAdd
    : expressionAdd PLUS expressionMul
    | expressionAdd MINUS expressionMul
    | expressionMul
    ;

/* Multiplicação, divisão e módulo. */
expressionMul
    : expressionMul MULT expressionUnary
    | expressionMul DIV expressionUnary
    | expressionMul MOD expressionUnary
    | expressionUnary
    ;

/* Operadores unários: negação lógica, negação aritmética ou expressão com possível cast. */
expressionUnary
    : NOT expressionUnary
    | MINUS expressionUnary
    | castExpr
    ;

/* Conversão explícita de tipo com possibilidade de encadeamento de casts. */
castExpr
    : LPAREN type RPAREN castExpr
    | primary
    ;

/* Unidade atómica de expressão: literais, identificadores, acessos a vetor, chamadas ou subexpressões. */
primary
    : LPAREN expression RPAREN
    | functionCall
    | IDENTIFIER
    | IDENTIFIER LBRACKET expression RBRACKET
    | NUMBER
    | REAL_NUM
    | STRING_LITERAL
    ;

/* Chamadas de função:
 * - funções definidas pelo utilizador
 * - funções de entrada embutidas (ler, lerc, lers)
 */
functionCall
    : IDENTIFIER LPAREN arguments? RPAREN
    | READ LPAREN RPAREN
    | READC LPAREN RPAREN
    | READS LPAREN RPAREN
    ;

/* Argumentos passados a funções. */
arguments
    : expression (COMMA expression)*
    ;

/* ---------- Instruções ---------- */

/* Bloco de instruções delimitado por chavetas. */
block
    : LBRACE statement* RBRACE
    ;

/* Regra principal de instrução, estruturada para resolver a ambiguidade do "dangling else". */
statement
    : IF LPAREN expression RPAREN block (ELSE block)?
    | whileStatement
    | forStatement
    | writeStatement
    | returnStatement
    | assignStatement
    | expressionStatement
    | declaration
    | block
    ;

/* Ciclo while. */
whileStatement
    : WHILE LPAREN expression RPAREN block
    ;

/* Ciclo 'para' com componentes opcionais: inicialização, condição e atualização. */
forStatement
    : FOR LPAREN expressionOrAssign? SEMI_COLON
                       expression? SEMI_COLON
                       expressionOrAssign? RPAREN block
    ;

/* Expressão que pode ser uma atribuição ou uma expressão simples (usada no ciclo 'para'). */
expressionOrAssign
    : (IDENTIFIER | IDENTIFIER LBRACKET expression RBRACKET) ASSIGN expression
    | expression
    ;

/* Instruções de saída (output) para valores numéricos, caracteres, vetores ou strings. */
writeStatement
    : WRITE LPAREN expression RPAREN SEMI_COLON
    | WRITEC LPAREN expression RPAREN SEMI_COLON
    | WRITEV LPAREN IDENTIFIER RPAREN SEMI_COLON
    | WRITES LPAREN stringArgument RPAREN SEMI_COLON
    ;

/* Retorno de função. */
returnStatement
    : RETURN expression? SEMI_COLON
    ;

/* Atribuição simples ou indexada. */
assignStatement
    : (IDENTIFIER | IDENTIFIER LBRACKET expression RBRACKET)
      ASSIGN expression SEMI_COLON
    ;

/* Expressão isolada. */
expressionStatement
    : expression SEMI_COLON
    ;

/* Argumento de string: literal ou identificador (esperado representar vetor de inteiros terminado em 0 — verificação externa). */
stringArgument
    : IDENTIFIER
    | STRING_LITERAL
    ;
