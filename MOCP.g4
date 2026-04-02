grammar MOCP;

/*
 * -----------
 * LEXER RULES
 * -----------
 */

// Tipos de dados suportados
INTEIRO : 'inteiro' ;        // tipo inteiro
REAL    : 'real' ;           // tipo real
VAZIO   : 'vazio' ;          // ausência de valor

// Função de entrada do programa
PRINCIPAL : 'principal' ;    // equivalente a 'main'

// Estruturas de controlo
SE      : 'se' ;             // condicional
SENAO   : 'senao' ;          // alternativa
ENQUANTO: 'enquanto' ;       // ciclo while
PARA    : 'para' ;           // ciclo for
RETORNAR: 'retornar' ;       // retorno de função

// Funções de leitura (input)
LER    : 'ler' ;             // leitura numérica
LERC   : 'lerc' ;            // leitura de caráter (ASCII)
LERS   : 'lers' ;            // leitura de string como vetor de inteiros (ASCII, terminada em 0)

// Funções de escrita (output)
ESCREVER   : 'escrever' ;    // escrita numérica
ESCREVERC  : 'escreverc' ;   // escrita de caráter
ESCREVERV  : 'escreverv' ;   // escrita de vetor
ESCREVERS  : 'escrevers' ;   // escrita de string

// Operadores aritméticos suportados (subconjunto de C)
MAIS    : '+' ;
MENOS   : '-' ;
MULT    : '*' ;
DIV     : '/' ;
MODULO  : '%' ;

// Operadores relacionais
MENOR       : '<' ;
MENORIGUAL  : '<=' ;
MAIOR       : '>' ;
MAIORIGUAL  : '>=' ;
IGUAL       : '==' ;
DIFERENTE   : '!=' ;

// Operadores lógicos
E_LOGICO    : '&&' ;
OU_LOGICO   : '||' ;
NAO         : '!' ;

// Símbolos e pontuação
ATRIBUICAO   : '=' ;
VIRGULA      : ',' ;
PONTOVIRG    : ';' ;
ABRECOLCH    : '[' ;
FECHACOLCH   : ']' ;
ABRECHAVES   : '{' ;
FECHACHAVES  : '}' ;
ABREPAR      : '(' ;
FECHAPAR     : ')' ;

// Literais e identificadores
STRINGLITERAL : '"' ( '\\' . | ~["\\\r\n] )* '"' ;  // string literal com escapes
NUM_REAL      : [0-9]+ '.' [0-9]+ ;                 // literal real
NUMERO        : [0-9]+ ;                            // literal inteiro
IDENTIFICADOR : [a-zA-Z_][a-zA-Z0-9_]* ;            // identificador válido

// Elementos ignorados
COMENTARIO_BLOCK : '/*' .*? '*/' -> skip ;          // comentário multi-linha
COMENTARIO_LINE  : '//' ~[\r\n]* -> skip ;          // comentário de linha
ESPACO : [ \t\r\n]+ -> skip ;                       // whitespace

/* =========================
 * PARSER
 * =========================
 *

/* ---------- Programa ---------- */

/* Estrutura global: protótipos seguidos do corpo executável. */
programa
    : prototipos corpo EOF
    ;

/* Conjunto de protótipos opcionais seguido obrigatoriamente do protótipo da função principal. */
prototipos
    : prototipo* prototipoPrincipal
    ;

/* Sequência de unidades (declarações ou funções) terminando obrigatoriamente na implementação da função principal. */
corpo
    : unidade* funcaoPrincipal
    ;

/* Elemento de topo do corpo: pode ser uma função definida ou uma declaração global. */
unidade
    : funcao
    | declaracao
    ;

/* ---------- Funções ---------- */

/* Assinatura de função sem corpo. */
prototipo
    : tipoRetorno IDENTIFICADOR ABREPAR parametros? FECHAPAR PONTOVIRG
    ;

/* Declaração obrigatória da função principal. */
prototipoPrincipal
    : VAZIO PRINCIPAL ABREPAR FECHAPAR PONTOVIRG
    ;

/* Implementação da função principal. */
funcaoPrincipal
    : VAZIO PRINCIPAL ABREPAR FECHAPAR bloco
    ;

/* Definição de função com corpo. */
funcao
    : tipoRetorno IDENTIFICADOR ABREPAR parametros? FECHAPAR bloco
    ;

/* Parâmetros formais: podem ser omitidos, explicitamente 'vazio', ou uma lista tipada de parâmetros. */
parametros
    : VAZIO
    | parametro (VIRGULA parametro)*
    ;

/* Parâmetro simples ou vetor. */
parametro
    : tipo IDENTIFICADOR
    | tipo IDENTIFICADOR ABRECOLCH FECHACOLCH
    ;

/* Tipos suportados pela linguagem. */
tipo
    : INTEIRO
    | REAL
    ;

tipoRetorno
    : INTEIRO
    | REAL
    | VAZIO
    ;

/* ---------- Declarações ---------- */

/* Declaração de variáveis, com ou sem inicialização. */
declaracao
    : tipo listaVariaveis PONTOVIRG
    ;

/* Conjunto de variáveis declaradas no mesmo contexto. */
listaVariaveis
    : variavel (VIRGULA variavel)*
    ;

/* Declaração de variável:
 * - escalar simples (com ou sem inicialização)
 * - vetor com tamanho fixo
 * - vetor com inferência via inicialização (lista ou leitura com lers)
 * Nota: lers() tem alternativa explícita pois infere o tamanho do vetor;
 * ler() e lerc() são tratados como expressões normais via chamadaFuncao.
 */
variavel
    : IDENTIFICADOR
    | IDENTIFICADOR ATRIBUICAO expressao
    | IDENTIFICADOR ABRECOLCH NUMERO FECHACOLCH
    | IDENTIFICADOR ABRECOLCH FECHACOLCH ATRIBUICAO LERS ABREPAR FECHAPAR
    | IDENTIFICADOR ABRECOLCH FECHACOLCH ATRIBUICAO blocoArray
    | IDENTIFICADOR ABRECOLCH NUMERO FECHACOLCH ATRIBUICAO blocoArray
    ;

/* Inicialização de vetor através de lista de expressões entre chavetas. */
blocoArray
    : ABRECHAVES listaValores? FECHACHAVES
    ;

/* Valores usados na inicialização de vetores. */
listaValores
    : expressao (VIRGULA expressao)*
    ;

/* ---------- Expressões ---------- */

/* Ponto de entrada da hierarquia de precedência das expressões. */
expressao
    : expressaoOr
    ;

/* Operador lógico OU (menor precedência). */
expressaoOr
    : expressaoOr OU_LOGICO expressaoAnd
    | expressaoAnd
    ;

/* Operador lógico E. */
expressaoAnd
    : expressaoAnd E_LOGICO expressaoEquality
    | expressaoEquality
    ;

/* Expressões com operadores de igualdade (==, !=), associativas à esquerda. */
expressaoEquality
    : expressaoRelacional
    | expressaoEquality opEquality expressaoRelacional
    ;

/* Operadores de igualdade. */
opEquality
    : IGUAL
    | DIFERENTE
    ;

/* Expressões com operadores relacionais (<, <=, >, >=). */
expressaoRelacional
    : expressaoAdd
    | expressaoRelacional opRelacional expressaoAdd
    ;

/* Operadores relacionais (<, <=, >, >=). */
opRelacional
    : MENOR
    | MENORIGUAL
    | MAIOR
    | MAIORIGUAL
    ;

/* Soma e subtração. */
expressaoAdd
    : expressaoAdd MAIS expressaoMul
    | expressaoAdd MENOS expressaoMul
    | expressaoMul
    ;

/* Multiplicação, divisão e módulo. */
expressaoMul
    : expressaoMul MULT expressaoUnaria
    | expressaoMul DIV expressaoUnaria
    | expressaoMul MODULO expressaoUnaria
    | expressaoUnaria
    ;

/* Operadores unários: negação lógica, negação aritmética ou expressão com possível cast. */
expressaoUnaria
    : NAO expressaoUnaria
    | MENOS expressaoUnaria
    | castExpr
    ;

/* Conversão explícita de tipo com possibilidade de encadeamento de casts. */
castExpr
    : ABREPAR tipo FECHAPAR castExpr
    | primary
    ;

/* Unidade atómica de expressão: literais, identificadores, acessos a vetor, chamadas ou subexpressões. */
primary
    : ABREPAR expressao FECHAPAR
    | chamadaFuncao
    | IDENTIFICADOR
    | IDENTIFICADOR ABRECOLCH expressao FECHACOLCH
    | NUMERO
    | NUM_REAL
    | STRINGLITERAL
    ;

/* Chamadas de função:
 * - funções definidas pelo utilizador
 * - funções de entrada embutidas (ler, lerc, lers)
 */
chamadaFuncao
    : IDENTIFICADOR ABREPAR argumentos? FECHAPAR
    | LER ABREPAR FECHAPAR
    | LERC ABREPAR FECHAPAR
    | LERS ABREPAR FECHAPAR
    ;

/* Argumentos passados a funções. */
argumentos
    : expressao (VIRGULA expressao)*
    ;

/* ---------- Instruções ---------- */

/* Bloco de instruções delimitado por chavetas. */
bloco
    : ABRECHAVES instrucao* FECHACHAVES
    ;

/* Regra principal de instrução, estruturada para resolver a ambiguidade do "dangling else". */
instrucao
    : SE ABREPAR expressao FECHAPAR bloco (SENAO bloco)?
    | instrucaoEnquanto
    | instrucaoPara
    | instrucaoEscrita
    | instrucaoReturn
    | instrucaoAtribuicao
    | instrucaoExpressao
    | declaracao
    | bloco
    ;

/* Ciclo while. */
instrucaoEnquanto
    : ENQUANTO ABREPAR expressao FECHAPAR bloco
    ;

/* Ciclo 'para' com componentes opcionais: inicialização, condição e atualização. */
instrucaoPara
    : PARA ABREPAR expressaoOuAtribuicao? PONTOVIRG 
                       expressao? PONTOVIRG 
                       expressaoOuAtribuicao? FECHAPAR bloco
    ;

/* Expressão que pode ser uma atribuição ou uma expressão simples (usada no ciclo 'para'). */
expressaoOuAtribuicao
    : (IDENTIFICADOR | IDENTIFICADOR ABRECOLCH expressao FECHACOLCH) ATRIBUICAO expressao
    | expressao
    ;

/* Instruções de saída (output) para valores numéricos, caracteres, vetores ou strings. */
instrucaoEscrita
    : ESCREVER ABREPAR expressao FECHAPAR PONTOVIRG
    | ESCREVERC ABREPAR expressao FECHAPAR PONTOVIRG
    | ESCREVERV ABREPAR IDENTIFICADOR FECHAPAR PONTOVIRG
    | ESCREVERS ABREPAR argumentoString FECHAPAR PONTOVIRG
    ;

/* Retorno de função. */
instrucaoReturn
    : RETORNAR expressao? PONTOVIRG
    ;

/* Atribuição simples ou indexada. */
instrucaoAtribuicao
    : (IDENTIFICADOR | IDENTIFICADOR ABRECOLCH expressao FECHACOLCH) 
      ATRIBUICAO expressao PONTOVIRG
    ;

/* Expressão isolada. */
instrucaoExpressao
    : expressao PONTOVIRG
    ;

/* Argumento de string: literal ou identificador (esperado representar vetor de inteiros terminado em 0 — verificação externa). */
argumentoString
    : IDENTIFICADOR
    | STRINGLITERAL
    ;
