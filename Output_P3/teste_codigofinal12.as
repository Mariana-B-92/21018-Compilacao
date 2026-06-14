; ============================================================
; Codigo P3 Assembly gerado pelo MOCP Compiler
; Simulador: https://p3js.goncalomb.com/
; ============================================================

STR_END         EQU      0000h
SP_INIT         EQU      FDFFh
TERM_W          EQU      FFFEh
TERM_S          EQU      FFFDh
TERM_R          EQU      FFFFh

                ORIG     0000h
                MOV      R1, SP_INIT
                MOV      SP, R1
                CALL     principal
FIM:            JMP      FIM

; ============================================================
;    Funcao: principal
; ============================================================
principal:      PUSH     R5
                MOV      R5, SP
                MOV      R2, SP
                SUB      R2, 6
                MOV      SP, R2
; ler() -> R1
                CALL     READ
                MOV      R4, R5
                SUB      R4, 1
                MOV      M[R4], R1
; ler() -> R1
                CALL     READ
                MOV      R4, R5
                SUB      R4, 2
                MOV      M[R4], R1
; i = 1
                MOV      R1, 1
                MOV      R4, R5
                SUB      R4, 3
                MOV      M[R4], R1
; t3 = i <= t1
L1:             MOV      R4, R5
                SUB      R4, 3
                MOV      R1, M[R4]
                MOV      R4, R5
                SUB      R4, 1
                MOV      R2, M[R4]
                CMP      R1, R2
                JMP.Z    L_asm_1
                JMP.N    L_asm_1
                MOV      R1, 0
                JMP      L_asm_2
L_asm_1:        MOV      R1, 1
L_asm_2:        MOV      R4, R5
                SUB      R4, 4
                MOV      M[R4], R1
; ifFalse t3 goto L2
                MOV      R4, R5
                SUB      R4, 4
                MOV      R1, M[R4]
                CMP      R1, R0
                JMP.Z    L2
; escrever(i)
                MOV      R4, R5
                SUB      R4, 3
                MOV      R1, M[R4]
                CALL     WRITE
; t4 = i + t2
                MOV      R4, R5
                SUB      R4, 3
                MOV      R1, M[R4]
                MOV      R4, R5
                SUB      R4, 2
                MOV      R2, M[R4]
                ADD      R1, R2
                MOV      R4, R5
                SUB      R4, 5
                MOV      M[R4], R1
; i = t4
                MOV      R4, R5
                SUB      R4, 5
                MOV      R1, M[R4]
                MOV      R4, R5
                SUB      R4, 3
                MOV      M[R4], R1
; goto L1
                JMP      L1
; halt
L2:             JMP      FIM

; ============================================================
;    Funcoes auxiliares de I/O (Terminal mapeado em memoria)
; ============================================================

; WRITES: escreve string em R1
WRITES:         MOV      R2, R1
WRITES_L1:      MOV      R1, M[R2]
                CMP      R1, R0
                JMP.Z    WRITES_END
                MOV      M[TERM_W], R1
                ADD      R2, 1
                JMP      WRITES_L1
WRITES_END:     RET

; WRITE: escreve inteiro em R1 seguido de newline
WRITE:          CMP      R1, R0
                JMP.Z    WRITE_ZERO
                JMP.N    WRITE_NEG
                MOV      R2, R1
                JMP      WRITE_POSITIVE
WRITE_ZERO:     MOV      R1, 48
                MOV      M[TERM_W], R1
                MOV      R1, 10
                MOV      M[TERM_W], R1
                RET
WRITE_NEG:      NEG      R1
                MOV      R2, R1
                MOV      R1, 45
                MOV      M[TERM_W], R1
WRITE_POSITIVE: MOV      R3, 0
WRITE_L1:       MOV      R4, 10
                DIV      R2, R4
                ADD      R4, 48
                PUSH     R4
                ADD      R3, 1
                CMP      R2, R0
                JMP.NZ   WRITE_L1
WRITE_L2:       POP      R1
                MOV      M[TERM_W], R1
                SUB      R3, 1
                CMP      R3, R0
                JMP.NZ   WRITE_L2
                MOV      R1, 10
                MOV      M[TERM_W], R1
                RET

; WRITEV: escreve vetor em R1 com formato {a,b,c} terminado em 0
WRITEV:         MOV      R2, R1
                MOV      R1, 123
                MOV      M[TERM_W], R1
                MOV      R1, M[R2]
                CMP      R1, R0
                JMP.Z    WRITEV_FECHA
WRITEV_L1:      PUSH     R2
                CALL     WRITE
                POP      R2
                ADD      R2, 1
                MOV      R1, M[R2]
                CMP      R1, R0
                JMP.Z    WRITEV_FECHA
WRITEV_VIRGULA: MOV      R3, 44
                MOV      M[TERM_W], R3
                JMP      WRITEV_L1
WRITEV_FECHA:   MOV      R1, 125
                MOV      M[TERM_W], R1
                MOV      R1, 10
                MOV      M[TERM_W], R1
                RET

; READC: le carater do terminal -> R1
READC:          MOV      R1, M[TERM_S]
                CMP      R1, R0
                JMP.Z    READC
                MOV      R1, M[TERM_R]
                MOV      M[TERM_W], R1
                RET

; READ: le inteiro do terminal -> R1
READ:           MOV      R2, R0
                MOV      R3, R0
READ_WAIT:      MOV      R1, M[TERM_S]
                CMP      R1, R0
                JMP.Z    READ_WAIT
                MOV      R1, M[TERM_R]
                MOV      M[TERM_W], R1
                MOV      R4, 13
                CMP      R1, R4
                JMP.Z    READ_FIM
                MOV      R4, 10
                CMP      R1, R4
                JMP.Z    READ_FIM
                MOV      R4, 45
                CMP      R1, R4
                JMP.NZ   READ_DIGITO
                MOV      R3, 1
                JMP      READ_WAIT
READ_DIGITO:    SUB      R1, 48
                MOV      R4, 10
                MUL      R2, R4
                MOV      R2, R4
                ADD      R2, R1
                JMP      READ_WAIT
READ_FIM:       CMP      R3, R0
                JMP.Z    READ_PRONTO
                NEG      R2
READ_PRONTO:    MOV      R1, R2
                RET

; READS: le string do terminal -> R1 (buffer STR_BUFFER)
READS:          MOV      R2, STR_BUFFER
READS_L1:       MOV      R1, M[TERM_S]
                CMP      R1, R0
                JMP.Z    READS_L1
                MOV      R1, M[TERM_R]
                MOV      M[TERM_W], R1
                MOV      R4, 13
                CMP      R1, R4
                JMP.Z    READS_END
                MOV      R4, 10
                CMP      R1, R4
                JMP.Z    READS_END
                MOV      M[R2], R1
                ADD      R2, 1
                JMP      READS_L1
READS_END:      MOV      M[R2], R0
                MOV      R1, STR_BUFFER
                RET

; ============================================================
; Seccao de Dados (ORIG 8000h)
; ============================================================

                ORIG     8000h


STR_BUFFER      TAB      256