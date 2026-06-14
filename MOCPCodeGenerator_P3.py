"""
Gerador de codigo final P3 Assembly a partir do TAC otimizado do compilador MOCP.

Arquitetura alvo: P3(16-bit, IST)
Simulador: https://p3js.goncalomb.com/

Registos:
  R0    : constante 0 (nao pode ser alterado)
  R1    : registo de resultado / valor de retorno de subrotinas
  R2-R4 : temporarios
  R5    : Frame Pointer (FP)
  SP    : Stack Pointer (registo especial, nao e R6)
  PC    : Program Counter (registo especial)

Convencao de chamada (com base na semantica P3 onde PUSH faz
M[SP]<-op; SP<-SP-1, portanto SP/FP apontam para a posicao LIVRE
acima do topo da pilha):

  FP+1 = FP antigo     (salvo pelo prologo com PUSH R5)
  FP+2 = endereco retorno  (empurrado pelo CALL)
  FP+3 = param_1       (primeiro argumento empurrado pelo caller)
  FP+4 = param_2
  ...
  FP-1 = 1a variavel local / temporario
  FP-2 = 2a variavel local / temporario
  ...

O prologo reserva N+1 slots (em vez de N) para que um PUSH subsequente
nao destrua o ultimo local: SP fica em FP-N-1 (livre), locais em FP-1..FP-N.

"""

from typing import List, Dict, Optional, Any

# ---------------------------------------------------------------------------
# Constantes P3
# ---------------------------------------------------------------------------
REG_ZERO   = "R0"
REG_RESULT = "R1"
REG_TMP1   = "R2"
REG_TMP2   = "R3"
REG_TMP3   = "R4"
REG_FP     = "R5"
REG_SP     = "SP"

# Terminal I/O via memoria mapeada (P3JS)
TERM_W_LBL    = "TERM_W"   # EQU 0FFFEh  porta de escrita
TERM_S_LBL    = "TERM_S"   # EQU 0FFFDh  estado (tecla disponivel?)
TERM_R_LBL    = "TERM_R"   # EQU 0FFFFh  porta de leitura

# Labels de funcoes auxiliares geradas no assembly
LBL_WRITE_STR = "WRITES"    # escreve string null-terminated em R1
LBL_WRITE_INT = "WRITE"    # escreve inteiro em R1
LBL_WRITE_VEC = "WRITEV"    # escreve vetor zero-terminated com chavetas
LBL_READ_CHAR = "READC"    # le carater -> R1
LBL_READ_INT  = "READ"    # le inteiro -> R1
LBL_READ_STR  = "READS"    # le string  -> R1 (endereco buffer)
LBL_STR_BUF   = "STR_BUFFER"    # buffer 256 palavras para lers()
LBL_HALT      = "FIM"  # loop infinito de halt
STR_BUF_SIZE  = 256

# Alinhamento das colunas no output
LABEL_WIDTH = 16   # largura reservada para a coluna do label
INSTR_WIDTH = 8    # largura do mnemonico


# ---------------------------------------------------------------------------
#       Funcao Geradora P3 Assembly a partir de quadruplos
# ---------------------------------------------------------------------------
def code_generator_p3(quadruplos: list) -> str:
    """
    Funcao de conveniencia: cria o gerador, processa as quadruplas e
    devolve o codigo P3 Assembly como string.
    """
    gen = MOCPCodeGenerator_P3(quadruplos)
    gen.generate()
    return gen.get_code()

# ---------------------------------------------------------------------------
#       Classe Geradora de codigo P3 Assembly
# ---------------------------------------------------------------------------
class MOCPCodeGenerator_P3:
    """
    Percorre a lista de quadruplas TAC e emite codigo P3 Assembly [P3JS]
    """
    def __init__(self, quadruplos: List[Dict]):
        self.quadruplos = quadruplos
        self._output: List[str] = []
        self._strings: Dict[str, str] = {}
        self._globais: set = set()
        self._lbl_counter = 0
        self._str_lbl_counter = 0

        self._current_func: Optional[str] = None
        self._func_vars: Dict[str, Dict[str, int]] = {}
        self._pending_params: List[str] = []
        self._pending_label: Optional[str] = None

        self._check_no_real()
        self._analyse_functions()

    # -----------------------------------------------------------------------
    #   Verificacao de tipo: o P3 nao tem unidade de virgula flutuante
    # -----------------------------------------------------------------------
    def _check_no_real(self):
        """
        Percorre o TAC e levanta um erro se encontrar valores 'real' (literais
        com ponto decimal ou casts para 'real'). O P3 trabalha apenas com
        inteiros de 16 bits, sem unidade de virgula flutuante, portanto nao
        e possivel gerar codigo para programas MOCP que usem 'real'.
        """
        def _has_real_literal(val):
            if val is None:
                return False
            s = str(val)
            # Cast para real aparece como "(real) ..." em arg1 dos quadruplos cast
            if s.startswith("(real)"):
                return True
            # Literal real: '3.14', '0.5', etc.
            try:
                int(s)
                return False
            except ValueError:
                pass
            try:
                float(s)
                # Confirma que tem ponto decimal (nao e um inteiro disfarcado)
                return "." in s
            except ValueError:
                return False

        for q in self.quadruplos:
            for field in ("arg1", "arg2"):
                if _has_real_literal(q.get(field)):
                    raise ValueError(
                        f"[Erro Geracao P3] Tipo 'real' nao e suportado pelo "
                        f"P3 (sem unidade de virgula flutuante). "
                        f"Operacao TAC encontrada: op={q.get('op')}, "
                        f"valor='{q.get(field)}'."
                    )

    # -----------------------------------------------------------------------
    #   Pre-processamento: identifica funcoes e calcula offsets FP
    # -----------------------------------------------------------------------
    def _analyse_functions(self):
        for q in self.quadruplos:
            if q["op"] == "label":
                lbl = q["res"]
                if self._is_function_label(lbl):
                    self._func_vars[lbl] = {}
        for fname in list(self._func_vars.keys()):
            self._compute_offsets(fname)

    def _compute_offsets(self, fname: str):
        """
        Calcula offsets FP para parametros, variaveis locais e temporarios.
          - param1 -> FP+3, param2 -> FP+4, ... (chamada com push em ordem inversa)
          - locais/temps -> FP-1, FP-2, ...
        """
        SKIP_OPS = {"label", "goto", "ifFalse", "param",
                    "halt", "write", "writec", "writev", "writes"}

        # Passo 1: descobrir parametros (paramN direto ou alias "v = paramN")
        named_params: dict = {}   # idx -> nome alias
        param_max = 0
        in_func = False

        for q in self.quadruplos:
            op = q["op"]
            if op == "label":
                if q["res"] == fname:
                    in_func = True
                    continue
                if in_func and self._is_function_label(q["res"]):
                    break
                continue
            if not in_func:
                continue

            if (op == "=" and isinstance(q.get("arg1"), str)
                    and q["arg1"].startswith("param") and q["arg1"][5:].isdigit()):
                idx = int(q["arg1"][5:])
                param_max = max(param_max, idx)
                named_params[idx] = q["res"]

            for field in ("arg1", "arg2"):
                val = q.get(field)
                if isinstance(val, str) and val.startswith("param") and val[5:].isdigit():
                    param_max = max(param_max, int(val[5:]))

        # No P3, PUSH faz M[SP]<-op; SP<-SP-1 (post-decrement), portanto SP/FP
        # apontam para a proxima posicao LIVRE (acima do topo). Apos
        # 'PUSH R5; MOV R5, SP':
        #   M[R5+1] = R5_antigo guardado
        #   M[R5+2] = endereco retorno do CALL
        #   M[R5+3] = primeiro argumento (empilhado pelo caller antes do CALL)
        #   M[R5+4] = segundo argumento, etc.
        # Por isso param1 -> FP+3, param2 -> FP+4, ...
        param_offsets: dict = {}
        for idx in range(1, param_max + 1):
            fp_off = idx + 2
            param_offsets[f"param{idx}"] = fp_off
            if idx in named_params:
                param_offsets[named_params[idx]] = fp_off

        # Passo 2: recolher locais e temporarios
        all_param_keys = set(param_offsets.keys())
        locals_list: list = []
        in_func = False

        for q in self.quadruplos:
            op = q["op"]
            if op == "label":
                if q["res"] == fname:
                    in_func = True
                    continue
                if in_func and self._is_function_label(q["res"]):
                    break
                continue
            if not in_func:
                continue

            res = q.get("res")
            if (res and isinstance(res, str)
                    and res not in all_param_keys
                    and res not in locals_list
                    and op not in SKIP_OPS):
                locals_list.append(res)

        self._func_vars[fname] = {
            **param_offsets,
            **{v: -(j) for j, v in enumerate(locals_list, start=1)},
        }

    # -----------------------------------------------------------------------
    # Emissao de comentarios P3
    #   Convencao do manual/assembler: um label fica colado a instrucao
    #   seguinte (nunca sozinho numa linha). Guardamos o label pendente
    #   e colamo-lo com a proxima instrucao emitida.
    # -----------------------------------------------------------------------

    def _p3_comment(self, comment: str):
        self._output.append(f"; {comment}")

    def _p3_queue_label(self, label: str):
        """
        Regista um label para ser colado na proxima instrucao emitida.
        Se ja havia um label pendente, emite-o com NOP para nao o perder.
        """
        if self._pending_label is not None:
            self._p3_flush_label("NOP")
        self._pending_label = label

    def _p3_flush_label(self, mnemonic: str, *operands):
        """
        Emite a instrucao com o label pendente (se existir) na mesma linha.
        Formato P3JS:  label:          INSTR    operandos
        """
        ops_str = ", ".join(str(o) for o in operands)
        instr_part = f"{mnemonic:<{INSTR_WIDTH}} {ops_str}".rstrip() if ops_str \
                     else f"{mnemonic}"

        if self._pending_label is not None:
            lbl_col = f"{self._pending_label}:"
            line = f"{lbl_col:<{LABEL_WIDTH}}{instr_part}"
            self._pending_label = None
        else:
            line = f"{' ' * LABEL_WIDTH}{instr_part}"

        self._output.append(line)

    def _p3_instr(self, mnemonic: str, *operands):
        self._p3_flush_label(mnemonic, *operands)

    def _p3_new_lbl(self) -> str:
        """Gera label interno de controlo de fluxo (LBL1, LBL2, ...)."""
        self._lbl_counter += 1
        return f"L_asm_{self._lbl_counter}"

    def _p3_new_str_lbl(self) -> str:
        """Gera label de string literal para a seccao de dados (STR1, STR2, ...)."""
        self._str_lbl_counter += 1
        return f"STR_LIT_{self._str_lbl_counter}"

    # -----------------------------------------------------------------------
    # Acesso a variaveis (load/store)
    # -----------------------------------------------------------------------

    def _p3_var_offset(self, name: str) -> Optional[int]:
        if self._current_func and name in self._func_vars.get(self._current_func, {}):
            return self._func_vars[self._current_func][name]
        return None

    def _p3_load_neg(self, abs_offset: int, dest_reg: str):
        """Carrega M[FP - abs_offset] em dest_reg. O manual so documenta o
        endereco indexado na forma M[Rx+W], pelo que o endereco e calculado
        num registo (evita-se a forma nao documentada M[R5-N])."""
        self._p3_instr("MOV", REG_TMP3, REG_FP)
        self._p3_instr("SUB", REG_TMP3, abs_offset)
        self._p3_instr("MOV", dest_reg, f"M[{REG_TMP3}]")

    def _p3_store_neg(self, abs_offset: int, src_reg: str):
        """Guarda src_reg em M[FP - abs_offset]. O manual so documenta o
        endereco indexado na forma M[Rx+W], pelo que o endereco e calculado
        num registo (evita-se a forma nao documentada M[R5-N])."""
        self._p3_instr("MOV", REG_TMP3, REG_FP)
        self._p3_instr("SUB", REG_TMP3, abs_offset)
        self._p3_instr("MOV", f"M[{REG_TMP3}]", src_reg)

    def _p3_sub_sp(self, n: int):
        """SP = SP - n. O manual so permite escrever no SP via MOV SP, R[1-7]
        (o SP nunca e operando de SUB/ADD), por isso opera-se num registo e
        copia-se o resultado de volta para o SP."""
        self._p3_instr("MOV", REG_TMP1, REG_SP)
        self._p3_instr("SUB", REG_TMP1, n)
        self._p3_instr("MOV", REG_SP, REG_TMP1)

    def _p3_add_sp(self, n: int):
        """SP = SP + n. O manual so permite escrever no SP via MOV SP, R[1-7]
        (o SP nunca e operando de SUB/ADD), por isso opera-se num registo e
        copia-se o resultado de volta para o SP."""
        self._p3_instr("MOV", REG_TMP1, REG_SP)
        self._p3_instr("ADD", REG_TMP1, n)
        self._p3_instr("MOV", REG_SP, REG_TMP1)

    def _p3_load(self, operand, dest_reg: str):
        """
        Carrega um operando em dest_reg. O operando pode ser:
          - None              -> carrega 0
          - inteiro literal   -> MOV dest, valor
          - string '"texto"'  -> regista a string e carrega o seu endereco
          - identificador     -> resolve via offset FP (parametro, local) ou
                                  endereco direto se for um simbolo externo
        """
        if operand is None:
            self._p3_instr("MOV", dest_reg, REG_ZERO)
            return

        if isinstance(operand, int):
            self._p3_instr("MOV", dest_reg, operand)
            return

        s = str(operand)

        try:
            self._p3_instr("MOV", dest_reg, int(s))
            return
        except ValueError:
            pass

        if s.startswith('"') and s.endswith('"'):
            lbl = self._p3_register_string(s[1:-1])
            self._p3_instr("MOV", dest_reg, lbl)
            return

        offset = self._p3_var_offset(s)
        if offset is not None:
            if offset >= 0:
                self._p3_instr("MOV", dest_reg, f"M[{REG_FP}+{offset}]")
            else:
                self._p3_load_neg(-offset, dest_reg)
        else:
            self._globais.add(s)
            self._p3_instr("MOV", dest_reg, f"M[{s}]")

    def _p3_store(self, dest: str, src_reg: str):
        """Guarda src_reg na variavel dest."""
        offset = self._p3_var_offset(dest)
        if offset is not None:
            if offset >= 0:
                self._p3_instr("MOV", f"M[{REG_FP}+{offset}]", src_reg)
            else:
                self._p3_store_neg(-offset, src_reg)
        else:
            self._globais.add(dest)
            self._p3_instr("MOV", f"M[{dest}]", src_reg)

    def _p3_register_string(self, content: str) -> str:
        for lbl, val in self._strings.items():
            if val == content:
                return lbl
        lbl = self._p3_new_str_lbl()
        self._strings[lbl] = content
        return lbl

    # -----------------------------------------------------------------------
    # Geracao principal
    # -----------------------------------------------------------------------

    def generate(self):
        self._output = []
        self._strings = {}
        self._globais = set()
        self._pending_params = []
        self._pending_label = None

        self._p3_comment("============================================================")
        self._p3_comment("Codigo P3 Assembly gerado pelo MOCP Compiler")
        self._p3_comment("Simulador: https://p3js.goncalomb.com/")
        self._p3_comment("============================================================")
        self._output.append("")

        # Constantes e portas (seguindo template P3JS; hex sem 0 inicial)
        self._output.append(f"{'STR_END':<{LABEL_WIDTH}}EQU      0000h")
        self._output.append(f"{'SP_INIT':<{LABEL_WIDTH}}EQU      FDFFh")
        self._output.append(f"{TERM_W_LBL:<{LABEL_WIDTH}}EQU      FFFEh")
        self._output.append(f"{TERM_S_LBL:<{LABEL_WIDTH}}EQU      FFFDh")
        self._output.append(f"{TERM_R_LBL:<{LABEL_WIDTH}}EQU      FFFFh")
        self._output.append("")

        # Regiao de codigo (0000h)
        self._p3_instr("ORIG", "0000h")
        # Inicializar SP conforme template P3JS
        self._p3_instr("MOV", "R1", "SP_INIT")
        self._p3_instr("MOV", "SP", "R1")
        self._p3_instr("CALL", "principal")
        self._p3_queue_label(LBL_HALT)
        self._p3_instr("JMP", LBL_HALT)
        self._output.append("")

        self._p3_functions()
        self._p3_emit_helpers()
        self._p3_data_section()

    def _p3_functions(self):
        for q in self.quadruplos:
            self._p3_quad(q)

    def _p3_quad(self, q: Dict):
        op:   Any = q.get("op")
        arg1: Any = q.get("arg1")
        arg2: Any = q.get("arg2")
        res:  Any = q.get("res")

        if op == "label":
            self._p3_label(res)

        elif op == "=":
            self._p3_comment(f"{res} = {arg1}")
            src_off = self._p3_var_offset(str(arg1)) if isinstance(arg1, str) else None
            dst_off = self._p3_var_offset(res)
            if src_off is None or dst_off is None or src_off != dst_off:
                self._p3_load(arg1, REG_RESULT)
                self._p3_store(res, REG_RESULT)

        elif op in {"+", "-", "*", "/", "%"}:
            self._p3_comment(f"{res} = {arg1} {op} {arg2}")
            self._p3_load(arg1, REG_RESULT)
            self._p3_load(arg2, REG_TMP1)
            if op == "+":
                self._p3_instr("ADD", REG_RESULT, REG_TMP1)
            elif op == "-":
                self._p3_instr("SUB", REG_RESULT, REG_TMP1)
            elif op == "*":
                # MUL op1, op2 deixa o resultado de 32 bits distribuido por
                # ambos os operandos: op1 contem o MSW e op2 o LSW. Para
                # multiplicacoes que cabem em 16 bits o resultado e o LSW,
                # que esta em REG_TMP1; copiamos para REG_RESULT.
                self._p3_instr("MUL", REG_RESULT, REG_TMP1)
                self._p3_instr("MOV", REG_RESULT, REG_TMP1)
            elif op == "/":
                self._p3_instr("DIV", REG_RESULT, REG_TMP1)
            elif op == "%":
                self._p3_instr("DIV", REG_RESULT, REG_TMP1)
                self._p3_instr("MOV", REG_RESULT, REG_TMP1)
            self._p3_store(res, REG_RESULT)

        elif op in {"==", "!=", "<", "<=", ">", ">="}:
            self._p3_comparison(op, arg1, arg2, res)

        elif op == "&&":
            self._p3_comment(f"{res} = {arg1} AND {arg2}")
            lbl_false = self._p3_new_lbl()
            lbl_end   = self._p3_new_lbl()
            self._p3_load(arg1, REG_RESULT)
            self._p3_instr("CMP",   REG_RESULT, REG_ZERO)
            self._p3_instr("JMP.Z", lbl_false)
            self._p3_load(arg2, REG_RESULT)
            self._p3_instr("CMP",   REG_RESULT, REG_ZERO)
            self._p3_instr("JMP.Z", lbl_false)
            self._p3_instr("MOV",   REG_RESULT, 1)
            self._p3_instr("JMP",   lbl_end)
            self._p3_queue_label(lbl_false)
            self._p3_instr("MOV",   REG_RESULT, 0)
            self._p3_queue_label(lbl_end)
            self._p3_store(res, REG_RESULT)

        elif op == "||":
            self._p3_comment(f"{res} = {arg1} OR {arg2}")
            lbl_true = self._p3_new_lbl()
            lbl_end  = self._p3_new_lbl()
            self._p3_load(arg1, REG_RESULT)
            self._p3_instr("CMP",    REG_RESULT, REG_ZERO)
            self._p3_instr("JMP.NZ", lbl_true)
            self._p3_load(arg2, REG_RESULT)
            self._p3_instr("CMP",    REG_RESULT, REG_ZERO)
            self._p3_instr("JMP.NZ", lbl_true)
            self._p3_instr("MOV",    REG_RESULT, 0)
            self._p3_instr("JMP",    lbl_end)
            self._p3_queue_label(lbl_true)
            self._p3_instr("MOV",    REG_RESULT, 1)
            self._p3_queue_label(lbl_end)
            self._p3_store(res, REG_RESULT)

        elif op == "minus":
            self._p3_comment(f"{res} = neg {arg1}")
            self._p3_load(arg1, REG_RESULT)
            self._p3_instr("NEG", REG_RESULT)
            self._p3_store(res, REG_RESULT)

        elif op == "not":
            self._p3_comment(f"{res} = not {arg1}")
            lbl_zero = self._p3_new_lbl()
            lbl_end  = self._p3_new_lbl()
            self._p3_load(arg1, REG_RESULT)
            self._p3_instr("CMP",   REG_RESULT, REG_ZERO)
            self._p3_instr("JMP.Z", lbl_zero)
            self._p3_instr("MOV",   REG_RESULT, 0)
            self._p3_instr("JMP",   lbl_end)
            self._p3_queue_label(lbl_zero)
            self._p3_instr("MOV",   REG_RESULT, 1)
            self._p3_queue_label(lbl_end)
            self._p3_store(res, REG_RESULT)

        elif op == "cast":
            self._p3_comment(f"{res} = cast {arg2}")
            self._p3_load(arg2, REG_RESULT)
            self._p3_store(res, REG_RESULT)

        elif op == "goto":
            self._p3_comment(f"goto {res}")
            self._p3_instr("JMP", res)

        elif op == "ifFalse":
            self._p3_comment(f"ifFalse {arg1} goto {res}")
            self._p3_load(arg1, REG_RESULT)
            self._p3_instr("CMP",   REG_RESULT, REG_ZERO)
            self._p3_instr("JMP.Z", res)

        elif op == "param":
            self._pending_params.append(arg1)

        elif op == "call":
            self._p3_call(arg1, int(arg2), res)

        elif op == "return":
            self._p3_return(arg1)

        elif op == "halt":
            self._p3_comment("halt")
            self._p3_instr("JMP", LBL_HALT)

        elif op == "write":
            self._p3_comment(f"escrever({arg1})")
            self._p3_load(arg1, REG_RESULT)
            self._p3_instr("CALL", LBL_WRITE_INT)

        elif op == "writec":
            self._p3_comment(f"escreverc({arg1})")
            self._p3_load(arg1, REG_RESULT)
            self._p3_instr("MOV", f"M[{TERM_W_LBL}]", REG_RESULT)

        elif op == "writes":
            self._p3_comment(f"escrevers({arg1})")
            raw = str(arg1)
            if raw.startswith('"') and raw.endswith('"'):
                lbl = self._p3_register_string(raw[1:-1])
                self._p3_instr("MOV", REG_RESULT, lbl)
            else:
                self._p3_load(arg1, REG_RESULT)
            self._p3_instr("CALL", LBL_WRITE_STR)

        elif op == "alloc":
            # Reserva N palavras consecutivas na pilha para um vetor e
            # guarda o seu endereco base em res. O TAC usa offsets em
            # "bytes virtuais" (i*4) para indexacao de vetores; as
            # operacoes [] e []= dividem o offset por 4 (SHR R, 2) para
            # converter para offset em palavras.
            n = int(arg1)
            self._p3_comment(f"alloc {res}[{n}] palavras")
            self._p3_instr("MOV", REG_RESULT, REG_SP)
            self._p3_instr("SUB", REG_RESULT, n)
            self._p3_instr("MOV", REG_SP, REG_RESULT)
            self._p3_store(res, REG_RESULT)

        elif op == "[]":
            # res = arr[offset]; offset esta em bytes virtuais (TAC),
            # convertido para palavras com SHR antes de somar ao endereco base.
            self._p3_comment(f"{res} = {arg1}[{arg2}]")
            self._p3_load(arg1, REG_TMP1)
            self._p3_load(arg2, REG_TMP2)
            self._p3_instr("SHR", REG_TMP2, 2)
            self._p3_instr("ADD", REG_TMP1, REG_TMP2)
            self._p3_instr("MOV", REG_RESULT, f"M[{REG_TMP1}]")
            self._p3_store(res, REG_RESULT)

        elif op == "[]=":
            # arr[offset] = val. arg1 e o offset (bytes virtuais), arg2 o
            # valor a guardar, res o nome do vetor (endereco base).
            self._p3_comment(f"{res}[{arg1}] = {arg2}")
            self._p3_load(res,  REG_TMP1)
            self._p3_load(arg1, REG_TMP2)
            self._p3_instr("SHR", REG_TMP2, 2)
            self._p3_instr("ADD", REG_TMP1, REG_TMP2)
            self._p3_load(arg2, REG_RESULT)
            self._p3_instr("MOV", f"M[{REG_TMP1}]", REG_RESULT)

        elif op == "writev":
            self._p3_comment(f"escreverv({arg1})")
            self._p3_load(arg1, REG_RESULT)
            self._p3_instr("CALL", LBL_WRITE_VEC)

        else:
            self._p3_comment(f"[NAO IMPLEMENTADO] op={op}")

    # -----------------------------------------------------------------------
    # Labels de funcao: prologo e epilogo
    # -----------------------------------------------------------------------

    def _p3_label(self, label: str):
        # Labels 'end_<funcao>' sao marcadores TAC do fim do corpo de uma
        # funcao. Emitimos um epilogo + RET aqui para que qualquer caminho
        # de execucao que chegue ao fim sem 'return' explicito retorne
        # correctamente. Excecao: 'end_principal' nao recebe epilogo porque
        # 'principal' termina sempre com 'halt'.
        if isinstance(label, str) and label.startswith("end_"):
            fname = label[4:]
            if fname != "principal":
                self._p3_comment(f"epilogo seguranca {fname}")
                self._p3_instr("MOV", REG_SP, REG_FP)
                self._p3_instr("POP", REG_FP)
                self._p3_instr("RET")
            return

        if self._is_function_label(label):
            self._current_func = label
            self._p3_comment("============================================================")
            self._p3_comment(f"   Funcao: {label}")
            self._p3_comment("============================================================")
            self._p3_queue_label(label)
            self._p3_instr("PUSH", REG_FP)
            self._p3_instr("MOV",  REG_FP, REG_SP)
            n_locals = self._count_locals(label)
            # Reservar N+1 slots em vez de N: SP fica num slot livre abaixo
            # do ultimo local, impedindo que PUSH subsequentes (passagem de
            # argumentos a funcoes chamadas) sobrescrevam variaveis locais.
            if n_locals > 0:
                self._p3_sub_sp(n_locals + 1)
        else:
            # Label de controlo de fluxo (L1, L2, ...): vai colado a
            # proxima instrucao emitida.
            self._p3_queue_label(label)

    def _count_locals(self, fname: str) -> int:
        return sum(1 for off in self._func_vars.get(fname, {}).values() if off < 0)

    # -----------------------------------------------------------------------
    # Comparacoes
    # -----------------------------------------------------------------------

    def _p3_comparison(self, op: str, arg1, arg2, res: str):
        self._p3_comment(f"{res} = {arg1} {op} {arg2}")
        self._p3_load(arg1, REG_RESULT)
        self._p3_load(arg2, REG_TMP1)
        self._p3_instr("CMP", REG_RESULT, REG_TMP1)

        lbl_true = self._p3_new_lbl()
        lbl_end  = self._p3_new_lbl()

        if op in {"<=", ">=", ">"}:
            self._p3_comparison_complex(op, lbl_true, lbl_end, res)
            return

        jmp_map = {"==": "JMP.Z", "!=": "JMP.NZ", "<": "JMP.N"}
        self._p3_instr(jmp_map[op], lbl_true)
        self._p3_instr("MOV", REG_RESULT, 0)
        self._p3_instr("JMP", lbl_end)
        self._p3_queue_label(lbl_true)
        self._p3_instr("MOV", REG_RESULT, 1)
        self._p3_queue_label(lbl_end)
        self._p3_store(res, REG_RESULT)

    def _p3_comparison_complex(self, op: str, lbl_true: str, lbl_end: str, res: str):
        """
        Comparacoes <=, >= e > com 2 condicoes (CMP ja emitido).
        Flags P3 apos CMP(a,b) = SUB(a,b):
          Z=1 -> a==b
          N=1 -> a<b  (resultado negativo)
        """
        if op == "<=":
            self._p3_instr("JMP.Z", lbl_true)
            self._p3_instr("JMP.N", lbl_true)
        elif op == ">":
            lbl_skip = self._p3_new_lbl()
            self._p3_instr("JMP.Z", lbl_skip)
            self._p3_instr("JMP.N", lbl_skip)
            self._p3_instr("JMP",   lbl_true)
            self._p3_queue_label(lbl_skip)
        elif op == ">=":
            lbl_skip = self._p3_new_lbl()
            self._p3_instr("JMP.Z", lbl_true)
            self._p3_instr("JMP.N", lbl_skip)
            self._p3_instr("JMP",   lbl_true)
            self._p3_queue_label(lbl_skip)

        self._p3_instr("MOV", REG_RESULT, 0)
        self._p3_instr("JMP", lbl_end)
        self._p3_queue_label(lbl_true)
        self._p3_instr("MOV", REG_RESULT, 1)
        self._p3_queue_label(lbl_end)
        self._p3_store(res, REG_RESULT)

    # -----------------------------------------------------------------------
    # Chamadas de funcao
    # -----------------------------------------------------------------------

    def _p3_call(self, func_name: str, n_args: int, res: str):
        params = self._pending_params[-n_args:] if n_args > 0 else []
        self._pending_params = self._pending_params[:-n_args] if n_args > 0 else self._pending_params

        if func_name == "ler":
            self._p3_comment("ler() -> R1")
            self._p3_instr("CALL", LBL_READ_INT)
            if res:
                self._p3_store(res, REG_RESULT)
            return

        if func_name == "lerc":
            self._p3_comment("lerc() -> R1")
            self._p3_instr("CALL", LBL_READ_CHAR)
            if res:
                self._p3_store(res, REG_RESULT)
            return

        if func_name == "lers":
            self._p3_comment("lers() -> R1 (endereco buffer)")
            self._p3_instr("CALL", LBL_READ_STR)
            if res:
                self._p3_store(res, REG_RESULT)
            return

        self._p3_comment(f"call {func_name}, {n_args}")
        for p in reversed(params):
            self._p3_load(p, REG_RESULT)
            self._p3_instr("PUSH", REG_RESULT)

        self._p3_instr("CALL", func_name)

        if n_args > 0:
            self._p3_add_sp(n_args)

        if res:
            self._p3_store(res, REG_RESULT)

    # -----------------------------------------------------------------------
    # Retorno
    # -----------------------------------------------------------------------

    def _p3_return(self, val):
        if val is not None:
            self._p3_comment(f"return {val}")
            self._p3_load(val, REG_RESULT)
        else:
            self._p3_comment("return")

        self._p3_instr("MOV", REG_SP, REG_FP)
        self._p3_instr("POP", REG_FP)
        self._p3_instr("RET")

    # -----------------------------------------------------------------------
    # Funcoes auxiliares de I/O geradas no assembly (terminal mapeado)
    # -----------------------------------------------------------------------

    def _p3_emit_helpers(self):
        self._output.append("")
        self._p3_comment("============================================================")
        self._p3_comment("   Funcoes auxiliares de I/O (Terminal mapeado em memoria)")
        self._p3_comment("============================================================")

        # --- WRITES: escreve string null-terminated; R1 = endereco ---
        # R2 = ponteiro (destruido); R1 = caracter corrente (destruido)
        self._output.append("")
        self._p3_comment(f"{LBL_WRITE_STR}: escreve string em R1")
        ws_loop = "WRITES_L1"
        ws_end  = "WRITES_END"
        self._p3_queue_label(LBL_WRITE_STR)
        self._p3_instr("MOV", "R2", "R1")
        self._p3_queue_label(ws_loop)
        self._p3_instr("MOV", "R1", "M[R2]")
        self._p3_instr("CMP", "R1", REG_ZERO)
        self._p3_instr("JMP.Z", ws_end)
        self._p3_instr("MOV", f"M[{TERM_W_LBL}]", "R1")
        self._p3_instr("ADD", "R2", 1)
        self._p3_instr("JMP", ws_loop)
        self._p3_queue_label(ws_end)
        self._p3_instr("RET")

        # --- WRITE: escreve inteiro com sinal seguido de \n; R1 = valor ---
        # R2 = valor absoluto, R3 = contador de digitos, R4 = temp
        self._output.append("")
        self._p3_comment(f"{LBL_WRITE_INT}: escreve inteiro em R1 seguido de newline")
        wi_zero = "WRITE_ZERO"
        wi_neg  = "WRITE_NEG"
        wi_ext  = "WRITE_POSITIVE"
        wi_loop = "WRITE_L1"
        wi_prt  = "WRITE_L2"
        self._p3_queue_label(LBL_WRITE_INT)
        self._p3_instr("CMP", "R1", REG_ZERO)
        self._p3_instr("JMP.Z", wi_zero)
        self._p3_instr("JMP.N", wi_neg)
        self._p3_instr("MOV", "R2", "R1")
        self._p3_instr("JMP", wi_ext)
        self._p3_queue_label(wi_zero)
        self._p3_instr("MOV", "R1", 48)
        self._p3_instr("MOV", f"M[{TERM_W_LBL}]", "R1")
        self._p3_instr("MOV", "R1", 10)
        self._p3_instr("MOV", f"M[{TERM_W_LBL}]", "R1")
        self._p3_instr("RET")
        self._p3_queue_label(wi_neg)
        self._p3_instr("NEG", "R1")
        self._p3_instr("MOV", "R2", "R1")
        self._p3_instr("MOV", "R1", 45)
        self._p3_instr("MOV", f"M[{TERM_W_LBL}]", "R1")
        self._p3_queue_label(wi_ext)
        self._p3_instr("MOV", "R3", 0)
        self._p3_queue_label(wi_loop)
        self._p3_instr("MOV", "R4", 10)
        self._p3_instr("DIV", "R2", "R4")      # R2=quociente, R4=resto(digito)
        self._p3_instr("ADD", "R4", 48)
        self._p3_instr("PUSH", "R4")
        self._p3_instr("ADD", "R3", 1)
        self._p3_instr("CMP", "R2", REG_ZERO)
        self._p3_instr("JMP.NZ", wi_loop)
        self._p3_queue_label(wi_prt)
        self._p3_instr("POP", "R1")
        self._p3_instr("MOV", f"M[{TERM_W_LBL}]", "R1")
        self._p3_instr("SUB", "R3", 1)
        self._p3_instr("CMP", "R3", REG_ZERO)
        self._p3_instr("JMP.NZ", wi_prt)
        self._p3_instr("MOV", "R1", 10)
        self._p3_instr("MOV", f"M[{TERM_W_LBL}]", "R1")
        self._p3_instr("RET")

        # --- WRITEV: escreve vetor no formato {n1,n2,...} terminado em 0 ---
        # R1 = endereco base do vetor (zero-terminated).
        # Imprime '{', depois cada inteiro do vetor separado por ','
        # (excepto o ultimo), termina com '}' e '\n'.
        # Registos destruidos: R1, R2 (ptr), R3 (val), R4 (temp).
        # Usa PUSH/POP em volta de chamadas a WRITE para nao perder o ptr.
        self._output.append("")
        self._p3_comment(f"{LBL_WRITE_VEC}: escreve vetor em R1 com formato"
                         " {a,b,c} terminado em 0")
        wv_loop  = "WRITEV_L1"
        wv_sep   = "WRITEV_VIRGULA"
        wv_end   = "WRITEV_FECHA"
        self._p3_queue_label(LBL_WRITE_VEC)
        self._p3_instr("MOV", "R2", "R1")                  # R2 = ponteiro
        self._p3_instr("MOV", "R1", 123)                    # '{'
        self._p3_instr("MOV", f"M[{TERM_W_LBL}]", "R1")
        # Primeiro elemento
        self._p3_instr("MOV", "R1", "M[R2]")
        self._p3_instr("CMP", "R1", REG_ZERO)
        self._p3_instr("JMP.Z", wv_end)                     # vazio: salta para '}'
        self._p3_queue_label(wv_loop)
        # Preserva o ponteiro R2 enquanto WRITE destroi registos.
        # Nota: WRITE imprime cada numero seguido de '\n', pelo que neste
        # formato os elementos saem em linhas separadas em vez de na
        # mesma linha {1,2,3}. Aceita-se este compromisso para reutilizar
        # WRITE sem duplicar a logica de impressao decimal.
        self._p3_instr("PUSH", "R2")
        self._p3_instr("CALL", LBL_WRITE_INT)
        self._p3_instr("POP", "R2")
        # Avanca para proximo elemento
        self._p3_instr("ADD", "R2", 1)
        self._p3_instr("MOV", "R1", "M[R2]")
        self._p3_instr("CMP", "R1", REG_ZERO)
        self._p3_instr("JMP.Z", wv_end)
        # Imprime virgula e continua
        self._p3_queue_label(wv_sep)
        self._p3_instr("MOV", "R3", 44)                     # ','
        self._p3_instr("MOV", f"M[{TERM_W_LBL}]", "R3")
        self._p3_instr("JMP", wv_loop)
        # Fim: imprime '}' e \n
        self._p3_queue_label(wv_end)
        self._p3_instr("MOV", "R1", 125)                    # '}'
        self._p3_instr("MOV", f"M[{TERM_W_LBL}]", "R1")
        self._p3_instr("MOV", "R1", 10)                     # '\n'
        self._p3_instr("MOV", f"M[{TERM_W_LBL}]", "R1")
        self._p3_instr("RET")

        # --- READC: le carater do terminal -> R1 (com echo) ---
        # loop ate tecla disponivel; R1 = estado/resultado
        self._output.append("")
        self._p3_comment(f"{LBL_READ_CHAR}: le carater do terminal -> R1")
        self._p3_queue_label(LBL_READ_CHAR)
        self._p3_instr("MOV", "R1", f"M[{TERM_S_LBL}]")
        self._p3_instr("CMP", "R1", REG_ZERO)
        self._p3_instr("JMP.Z", LBL_READ_CHAR)
        self._p3_instr("MOV", "R1", f"M[{TERM_R_LBL}]")
        self._p3_instr("MOV", f"M[{TERM_W_LBL}]", "R1")
        self._p3_instr("RET")

        # --- READ: le inteiro do terminal -> R1 ---
        # R2 = acumulador, R3 = sinal (0=pos, 1=neg), R4 = temp
        self._output.append("")
        self._p3_comment(f"{LBL_READ_INT}: le inteiro do terminal -> R1")
        ri_key    = "READ_WAIT"
        ri_nominus = "READ_DIGITO"
        ri_end    = "READ_FIM"
        ri_done   = "READ_PRONTO"
        self._p3_queue_label(LBL_READ_INT)
        self._p3_instr("MOV", "R2", REG_ZERO)
        self._p3_instr("MOV", "R3", REG_ZERO)
        self._p3_queue_label(ri_key)
        self._p3_instr("MOV", "R1", f"M[{TERM_S_LBL}]")
        self._p3_instr("CMP", "R1", REG_ZERO)
        self._p3_instr("JMP.Z", ri_key)
        self._p3_instr("MOV", "R1", f"M[{TERM_R_LBL}]")
        self._p3_instr("MOV", f"M[{TERM_W_LBL}]", "R1")
        self._p3_instr("MOV", "R4", 13)
        self._p3_instr("CMP", "R1", "R4")
        self._p3_instr("JMP.Z", ri_end)
        self._p3_instr("MOV", "R4", 10)
        self._p3_instr("CMP", "R1", "R4")
        self._p3_instr("JMP.Z", ri_end)
        self._p3_instr("MOV", "R4", 45)
        self._p3_instr("CMP", "R1", "R4")
        self._p3_instr("JMP.NZ", ri_nominus)
        self._p3_instr("MOV", "R3", 1)
        self._p3_instr("JMP", ri_key)
        self._p3_queue_label(ri_nominus)
        self._p3_instr("SUB", "R1", 48)
        self._p3_instr("MOV", "R4", 10)
        # MUL deixa MSW em R2 e LSW em R4; usamos R4 como novo acumulador.
        self._p3_instr("MUL", "R2", "R4")
        self._p3_instr("MOV", "R2", "R4")
        self._p3_instr("ADD", "R2", "R1")
        self._p3_instr("JMP", ri_key)
        self._p3_queue_label(ri_end)
        self._p3_instr("CMP", "R3", REG_ZERO)
        self._p3_instr("JMP.Z", ri_done)
        self._p3_instr("NEG", "R2")
        self._p3_queue_label(ri_done)
        self._p3_instr("MOV", "R1", "R2")
        self._p3_instr("RET")

        # --- READS: le string do terminal -> R1 = endereco buffer STR_BUFFER ---
        # R2 = ponteiro no buffer, R1 = caracter, R4 = temp
        self._output.append("")
        self._p3_comment(f"{LBL_READ_STR}: le string do terminal -> R1 (buffer {LBL_STR_BUF})")
        rs_key = "READS_L1"
        rs_end = "READS_END"
        self._p3_queue_label(LBL_READ_STR)
        self._p3_instr("MOV", "R2", LBL_STR_BUF)
        self._p3_queue_label(rs_key)
        self._p3_instr("MOV", "R1", f"M[{TERM_S_LBL}]")
        self._p3_instr("CMP", "R1", REG_ZERO)
        self._p3_instr("JMP.Z", rs_key)
        self._p3_instr("MOV", "R1", f"M[{TERM_R_LBL}]")
        self._p3_instr("MOV", f"M[{TERM_W_LBL}]", "R1")
        self._p3_instr("MOV", "R4", 13)
        self._p3_instr("CMP", "R1", "R4")
        self._p3_instr("JMP.Z", rs_end)
        self._p3_instr("MOV", "R4", 10)
        self._p3_instr("CMP", "R1", "R4")
        self._p3_instr("JMP.Z", rs_end)
        self._p3_instr("MOV", "M[R2]", "R1")
        self._p3_instr("ADD", "R2", 1)
        self._p3_instr("JMP", rs_key)
        self._p3_queue_label(rs_end)
        self._p3_instr("MOV", "M[R2]", REG_ZERO)
        self._p3_instr("MOV", "R1", LBL_STR_BUF)
        self._p3_instr("RET")

    # -----------------------------------------------------------------------
    # Seccao de dados (strings)
    # -----------------------------------------------------------------------

    def _p3_data_section(self):
        # Regiao de dados em 8000h (conforme template P3JS)
        self._output.append("")
        self._p3_comment("============================================================")
        self._p3_comment("Seccao de Dados (ORIG 8000h)")
        self._p3_comment("============================================================")
        self._output.append("")
        self._p3_instr("ORIG", "8000h")
        self._output.append("")

        for label, content in self._strings.items():
            # STR usa aspas simples no P3JS; sequencias de escape tornam-se
            # literais numericos: "ola\nmundo" -> STR 'ola', 10, 'mundo', STR_END
            parts = []
            buf = []
            i = 0
            while i < len(content):
                c = content[i]
                if c == '\\' and i + 1 < len(content):
                    nc = content[i + 1]
                    esc = {'n': 10, 't': 9, '\\': ord('\\'), "'": ord("'")}.get(nc)
                    if esc is not None:
                        if buf:
                            parts.append(f"'{''.join(buf)}'")
                            buf = []
                        parts.append(str(esc))
                        i += 2
                        continue
                buf.append(c)
                i += 1
            if buf:
                parts.append(f"'{''.join(buf)}'")
            parts.append("STR_END")

            # Labels de dados sem ':' (como no manual para WORD/STR/TAB)
            line = f"{label:<{LABEL_WIDTH}}STR      {', '.join(parts)}"
            self._output.append(line)

        # Variaveis globais / locais lidas sem nunca terem sido atribuidas são
        # declaradas com WORD 0 para que a etiqueta exista e o valor por omissao seja
        # 0, conforme a semantica da linguagem.
        reservados = {"STR_END", "SP_INIT", TERM_W_LBL, TERM_S_LBL, TERM_R_LBL,
                      LBL_STR_BUF}
        globais = sorted(n for n in self._globais
                         if n not in reservados and n not in self._strings)
        if globais:
            self._output.append("")
            for nome in globais:
                self._output.append(f"{nome:<{LABEL_WIDTH}}WORD     0")

        # Buffer estatico para lers()
        self._output.append("")
        self._output.append(f"{LBL_STR_BUF:<{LABEL_WIDTH}}TAB      {STR_BUF_SIZE}")

    # -----------------------------------------------------------------------
    #   Output final
    # -----------------------------------------------------------------------

    def get_code(self) -> str:
        return "\n".join(self._output)


    # ---------------------------------------------------------------------------
    #   Funcoes auxiliares
    # ---------------------------------------------------------------------------

    def _is_function_label(self, label: str) -> bool:
        if not isinstance(label, str):
            return False
        if label.startswith("_"):
            return False
        if label.startswith("L") and label[1:].isdigit():
            return False
        # LBL: labels internos de controlo de fluxo gerados para o P3
        if label.startswith("L_asm_"):
            return False
        # STR: labels de strings literais gerados para a seccao de dados
        if label.startswith("STR_LIT_"):
            return False
        if label.startswith("__"):
            return False
        # end_<funcao>: marcador de fim de funcao no TAC do MOCP, nao e uma nova funcao
        if label.startswith("end_"):
            return False
        return True