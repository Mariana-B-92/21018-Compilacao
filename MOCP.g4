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

/* PALAVRAS RESERVADAS DE C (proibidas — geram erro) */
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
