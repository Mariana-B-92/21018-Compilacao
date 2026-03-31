grammar MOCP;

/*
 * ----------------------------
 * LEXER RULES (tokens básicos)
 * ----------------------------
 */

// Tipos de dados suportados
INTEIRO : 'inteiro' ;        // tipo inteiro
REAL    : 'real' ;           // tipo real (ponto flutuante)
VAZIO   : 'vazio' ;          // ausência de valor de retorno

// Função de entrada do programa
PRINCIPAL : 'principal' ;    // equivalente a 'main'

// Funções de leitura (input)
LER    : 'ler' ;             // leitura numérica (inteiro ou real)
LERC   : 'lerc' ;            // leitura de um caráter (ASCII)
LERS   : 'lers' ;            // leitura de string (terminada em 0)

// Funções de escrita (output)
ESCREVER   : 'escrever' ;    // escrita numérica
ESCREVERC  : 'escreverc' ;   // escrita de caráter
ESCREVERV  : 'escreverv' ;   // escrita de vetor
ESCREVERS  : 'escrevers' ;   // escrita de string

// Estruturas de controlo
SE      : 'se' ;
SENAO   : 'senao' ;
ENQUANTO: 'enquanto' ;
PARA    : 'para' ;

// Operadores aritméticos
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

// Palavra-chave de retorno
RETORNAR : 'retornar' ;

// String literal (usada em escrevers)
STRINGLITERAL : '"' (~["\r\n])* '"' ;

// Comentários ignorados pelo parser
COMENTARIO_BLOCK : '/*' .*? '*/' -> skip ; // comentário multi-linha
COMENTARIO_LINE  : '//' ~[\r\n]* -> skip ; // comentário de linha

// Literais e identificadores
NUM_REAL : [0-9]+ '.' [0-9]+ ;             // número real
NUMERO   : [0-9]+ ;                        // número inteiro
IDENTIFICADOR : [a-zA-Z_][a-zA-Z0-9_]* ;   // identificador válido

// Espaços ignorados
ESPACO : [ \t\r\n]+ -> skip ;

/* =========================
 * PARSER
 * =========================
 */

programa
    : prototipo* declaracaoGlobal* funcao* funcaoPrincipal EOF
    ;

/* -------- PROTÓTIPOS -------- */

prototipo
    : tipoFunc IDENTIFICADOR ABREPAR parametrosProto? FECHAPAR PONTOVIRG
    ;

parametrosProto
    : parametroProto (VIRGULA parametroProto)*
    ;

parametroProto
    : tipoVar (ABRECOLCH FECHACOLCH)?
    ;

/* -------- DECLARAÇÕES GLOBAIS -------- */

declaracaoGlobal
    : tipoVar listaVariaveis PONTOVIRG
    ;

/* -------- FUNÇÕES -------- */

funcao
    : tipoFunc IDENTIFICADOR ABREPAR parametros? FECHAPAR bloco
    ;

funcaoPrincipal
    : VAZIO PRINCIPAL ABREPAR VAZIO? FECHAPAR bloco
    ;

/* Parâmetros */

parametros
    : parametro (VIRGULA parametro)*
    ;

parametro
    : tipoVar IDENTIFICADOR (ABRECOLCH FECHACOLCH)?
    ;

/* -------- DECLARAÇÕES LOCAIS -------- */

declaracao
    : tipoVar listaVariaveis PONTOVIRG
    ;

listaVariaveis
    : variavel (VIRGULA variavel)*
    ;

variavel
    : IDENTIFICADOR varSufixo?
    ;

varSufixo
    : ABRECOLCH expressao FECHACOLCH
    | ABRECOLCH FECHACOLCH (ATRIBUICAO inicializacaoVetor)?
    | ATRIBUICAO inicializacaoEscalar
    ;

/* Inicializações */

inicializacaoEscalar
    : LER ABREPAR FECHAPAR
    | LERC ABREPAR FECHAPAR
    | expressao
    ;

inicializacaoVetor
    : ABRECHAVES (expressao (VIRGULA expressao)*)? FECHACHAVES
    | LERS ABREPAR FECHAPAR
    ;

/* -------- EXPRESSÕES -------- */

expressao
    : expressaoAdd
    ;

expressaoAdd
    : expressaoMul ((MAIS | MENOS) expressaoMul)*
    ;

expressaoMul
    : expressaoUnaria ((MULT | DIV | MODULO) expressaoUnaria)*
    ;

expressaoUnaria
    : NAO expressaoUnaria
    | MENOS expressaoUnaria
    | expressaoCast
    ;

expressaoCast
    : ABREPAR tipoVar FECHAPAR expressaoCast
    | primary
    ;

primary
    : IDENTIFICADOR
    | IDENTIFICADOR ABREPAR argumentos? FECHAPAR
    | IDENTIFICADOR ABRECOLCH expressao FECHACOLCH
    | NUM_REAL
    | NUMERO
    | ABREPAR expressao FECHAPAR
    | LER ABREPAR FECHAPAR
    | LERC ABREPAR FECHAPAR
    | LERS ABREPAR FECHAPAR
    ;

/* Argumentos */

argumentos
    : expressao (VIRGULA expressao)*
    ;

/* -------- CONDIÇÕES -------- */

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

condicaoBase
    : ABREPAR condicao FECHAPAR
    | expressao (opRelacional expressao)?
    ;

opRelacional
    : MENOR | MENORIGUAL | MAIOR | MAIORIGUAL | IGUAL | DIFERENTE
    ;

/* -------- BLOCOS -------- */

bloco
    : ABRECHAVES instrucao* FECHACHAVES
    ;

/* -------- INSTRUÇÕES -------- */

instrucao
    : instrucaoSe
    | instrucaoEnquanto
    | instrucaoPara
    | instrucaoEscrita
    | instrucaoRetornar
    | atribuicao
    | declaracao
    | expressao PONTOVIRG
    ;

/* -------- INSTRUÇÕES SIMPLES -------- */

atribuicao
    : IDENTIFICADOR (ABRECOLCH expressao FECHACOLCH)? ATRIBUICAO expressao PONTOVIRG
    ;

/* -------- CONTROLO -------- */

instrucaoSe
    : SE ABREPAR condicao FECHAPAR bloco (SENAO bloco)?
    ;

instrucaoEnquanto
    : ENQUANTO ABREPAR condicao FECHAPAR bloco
    ;

instrucaoPara
    : PARA ABREPAR
        atribuicaoPara? PONTOVIRG
        condicao? PONTOVIRG
        atribuicaoPara?
      FECHAPAR bloco
    ;

atribuicaoPara
    : IDENTIFICADOR (ABRECOLCH expressao FECHACOLCH)? ATRIBUICAO expressao
    ;

/* -------- ESCRITA -------- */

instrucaoEscrita
    : ESCREVER  ABREPAR expressao FECHAPAR PONTOVIRG
    | ESCREVERC ABREPAR expressao FECHAPAR PONTOVIRG
    | ESCREVERV ABREPAR IDENTIFICADOR FECHAPAR PONTOVIRG
    | ESCREVERS ABREPAR argumentoString FECHAPAR PONTOVIRG
    ;

argumentoString
    : IDENTIFICADOR
    | STRINGLITERAL
    ;

/* -------- RETURN -------- */

instrucaoRetornar
    : RETORNAR expressao? PONTOVIRG
    ;

/* -------- TIPOS -------- */

tipoVar  : INTEIRO | REAL ;
tipoFunc : INTEIRO | REAL | VAZIO ;
