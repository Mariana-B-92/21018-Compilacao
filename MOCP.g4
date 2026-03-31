grammar MOCP;

/* =========================
 * LEXER
 * =========================
 * Tokens da linguagem MOCP (palavras-chave em português)
 */

/* Tipos e função principal */
INTEIRO   : 'inteiro' ;
REAL      : 'real' ;
VAZIO     : 'vazio' ;
PRINCIPAL : 'principal' ;

/* Funções de leitura */
LER       : 'ler' ;
LERC      : 'lerc' ;
LERS      : 'lers' ;

/* Funções de escrita */
ESCREVER  : 'escrever' ;
ESCREVERC : 'escreverc' ;
ESCREVERV : 'escreverv' ;
ESCREVERS : 'escrevers' ;

/* Controlo */
SE        : 'se' ;
SENAO     : 'senao' ;
ENQUANTO  : 'enquanto' ;
PARA      : 'para' ;
RETORNAR  : 'retornar' ;

/* Palavras de C proibidas */
ERRO_PALAVRA_C
    : 'int' | 'double' | 'void' | 'main'
    | 'if' | 'else' | 'while' | 'for' | 'return'
    | 'char' | 'float' | 'long' | 'short'
    | 'struct' | 'typedef' | 'sizeof'
    ;

/* Operadores não permitidos */
ERRO_OPERADORES_C
    : '++' | '--'
    | '+=' | '-=' | '*=' | '/='
    | '<<' | '>>'
    ;

/* Operadores */
MAIS : '+' ;
MENOS : '-' ;
MULT : '*' ;
DIV : '/' ;
MODULO : '%' ;

MENORIGUAL : '<=' ;
MAIORIGUAL : '>=' ;
MENOR : '<' ;
MAIOR : '>' ;
IGUAL : '==' ;
DIFERENTE : '!=' ;

E_LOGICO : '&&' ;
OU_LOGICO : '||' ;
NAO : '!' ;

/* Símbolos */
ATRIBUICAO : '=' ;
VIRGULA : ',' ;
PONTOVIRG : ';' ;

ABRECOLCH : '[' ;
FECHACOLCH : ']' ;
ABRECHAVES : '{' ;
FECHACHAVES : '}' ;
ABREPAR : '(' ;
FECHAPAR : ')' ;

/* Literais */
STRINGLITERAL : '"' (ESC_SEQ | ~["\\\r\n])* '"' ;
fragment ESC_SEQ : '\\' [\\'"nrt0] ;

NUM_REAL : [0-9]+ '.' [0-9]+ ;
NUMERO : [0-9]+ ;

IDENTIFICADOR : [a-zA-Z_][a-zA-Z0-9_]* ;

/* Ignorar */
COMENTARIO_BLOCK : '/*' .*? '*/' -> skip ;
COMENTARIO_LINE  : '//' ~[\r\n]* -> skip ;
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
