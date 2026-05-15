import copy
from typing import List, Dict, Set, Optional, Tuple
from collections import defaultdict

# ---------------------------------------------------------------------------
# Tipos auxiliares
# ---------------------------------------------------------------------------
Quadrupla = Dict  # {"op": str, "arg1": ..., "arg2": ..., "res": ...}
TAC = List[Quadrupla]

DEBUG_MODE = False


def _debug(*args):
    if DEBUG_MODE:
        print("DEBUG:", *args)


# ---------------------------------------------------------------------------
# Funções utilitárias
# ---------------------------------------------------------------------------

def _is_literal(operand) -> bool:
    """Verifica se um operando é um valor numérico ou booleano literal."""
    return isinstance(operand, (int, float, bool))


def _resolve_operand(operand, constant_map: dict):
    """
    Tenta obter o valor constante de um operando.
    Procura primeiro como literal numérico, depois no mapa de constantes.
    Retorna (valor, é_constante).
    """
    if isinstance(operand, str):
        try:
            return int(operand), True
        except ValueError:
            pass
        try:
            return float(operand), True
        except ValueError:
            pass
        if operand in constant_map:
            return constant_map[operand], True
        return operand, False

    if _is_literal(operand):
        return operand, True

    return operand, False


def _avaliar_op(op: str, v1, v2):
    """Avalia uma operação aritmética ou relacional entre dois literais."""
    ops = {
        "+": lambda a, b: a + b,
        "-": lambda a, b: a - b,
        "*": lambda a, b: a * b,
        "/": lambda a, b: a / b,
        "%": lambda a, b: a % b,
        "==": lambda a, b: a == b,
        "!=": lambda a, b: a != b,
        "<":  lambda a, b: a < b,
        "<=": lambda a, b: a <= b,
        ">":  lambda a, b: a > b,
        ">=": lambda a, b: a >= b,
    }
    if op in ops:
        return ops[op](v1, v2)
    raise ValueError(f"Operação desconhecida: {op}")


def _detectar_variaveis_de_ciclo(quadruplos: TAC) -> Set[str]:
    """
    Identifica variáveis modificadas dentro de ciclos, usando deteção de back-edges.

    Um back-edge é um salto (goto ou ifFalse) para um label que aparece
    antes dele na sequência — sinal de um ciclo. Todas as variáveis
    atribuídas entre esse label e o salto de volta são variáveis de ciclo.

    Estas variáveis não devem ser dobradas pelo constant folding nem
    eliminadas pelo dead code elimination, pois o seu valor muda a cada
    iteração.
    """
    label_pos: Dict[str, int] = {
        q["res"]: i
        for i, q in enumerate(quadruplos)
        if q["op"] == "label" and isinstance(q.get("res"), str)
    }

    vars_ciclo: Set[str] = set()

    for i, q in enumerate(quadruplos):
        if q["op"] not in {"goto", "ifFalse"}:
            continue
        target = q.get("res")
        if not isinstance(target, str) or target not in label_pos:
            continue
        start, end = label_pos[target], i
        if start >= end:
            continue  # salto para a frente — não é back-edge

        for q2 in quadruplos[start:end + 1]:
            if isinstance(q2.get("res"), str) and q2["op"] not in {"label", "goto", "ifFalse"}:
                vars_ciclo.add(q2["res"])

    return vars_ciclo


# ---------------------------------------------------------------------------
# Bloco Básico — unidade do CFG
# ---------------------------------------------------------------------------

class BlocoBasico:
    """
    Sequência máxima de instruções sem saltos intermédios.
    Usado na construção do grafo de fluxo de controlo (CFG).
    """

    def __init__(self, id_bloco: int, inicio_idx: int):
        self.id_bloco: int = id_bloco
        self.inicio_idx: int = inicio_idx
        self.fim_idx: int = -1
        self.quadruplas: TAC = []
        self.sucessores: List[int] = []

    def __repr__(self):
        return (f"Bloco(id={self.id_bloco}, "
                f"quads=[{self.inicio_idx}-{self.fim_idx}], "
                f"suc={self.sucessores})")


# ---------------------------------------------------------------------------
# Otimizador
# ---------------------------------------------------------------------------

class MOCPCodeOptimiser:
    """
    Otimiza o TAC gerado pelo MOCPIntermediateCodeGenerator.

    Técnicas aplicadas (por ordem):
        1. Constant Folding       — avalia expressões com operandos constantes
        2. Propagação de Cópias   — elimina atribuições redundantes (x = y)
        3. CSE                    — reutiliza subexpressões já calculadas
        4. LICM                   — move invariantes para fora dos ciclos
        5. Código Inatingível     — remove blocos não alcançáveis pelo CFG
        6. Código Morto           — remove instruções cujo resultado nunca é usado
    """

    def __init__(self, quadruplos: TAC, variaveis_utilizador: Optional[Set[str]] = None):
        self.quadruplos: TAC = copy.deepcopy(quadruplos)
        self.variaveis_utilizador: Set[str] = variaveis_utilizador or set()

        # Estado interno do CFG (construído sob demanda)
        self.blocos: List[BlocoBasico] = []
        self.mapa_labels_para_id_bloco: Dict[str, int] = {}
        self.mapa_idx_lider_para_id_bloco: Dict[int, int] = {}

    # -----------------------------------------------------------------------
    # API pública
    # -----------------------------------------------------------------------

    def optimise(self) -> TAC:
        """Aplica todas as otimizações por ordem, com ponto fixo onde necessário."""
        _debug("=== Início das Otimizações ===")

        self.constant_folding()
        self.propagacao_copias()
        self.eliminar_subexpressoes_comuns()
        self.mover_invariantes()
        self.constant_folding()        # 2ª passagem — aproveita propagações anteriores
        self.propagacao_copias()
        self.eliminar_codigo_inatingivel()

        # Código morto: repete até estabilizar
        prev = None
        atual = self.eliminar_codigo_morto()
        while prev != atual:
            prev = atual
            atual = self.eliminar_codigo_morto()

        _debug("=== Fim das Otimizações ===")
        return self.quadruplos

    # -----------------------------------------------------------------------
    # 1. Constant Folding
    # -----------------------------------------------------------------------

    def constant_folding(self) -> TAC:
        """
        Substitui operações binárias com operandos constantes pelo resultado.
        Itera até não haver mais alterações (ponto fixo).

        Não dobra expressões que envolvam variáveis de ciclo, pois o seu
        valor muda a cada iteração — dobrá-las produziria código incorreto.
        """
        ops_binarias = {"+", "-", "*", "/", "%", "==", "!=", "<", "<=", ">", ">="}

        fez_alteracoes = True
        while fez_alteracoes:
            fez_alteracoes = False
            novos = []
            constantes: Dict = {}
            vars_ciclo = _detectar_variaveis_de_ciclo(self.quadruplos)

            for q in self.quadruplos:
                op   = q["op"]
                arg1 = q.get("arg1")
                arg2 = q.get("arg2")
                res  = q.get("res")

                # Não resolve operandos de ciclo como constantes
                v1, c1 = (_resolve_operand(arg1, constantes)
                          if arg1 is not None and arg1 not in vars_ciclo
                          else (arg1, False))
                v2, c2 = (_resolve_operand(arg2, constantes)
                          if arg2 is not None and arg2 not in vars_ciclo
                          else (arg2, False))

                if op in ops_binarias and c1 and c2:
                    try:
                        resultado = _avaliar_op(op, v1, v2)
                        constantes[res] = resultado
                        novos.append({"op": "=", "arg1": resultado, "arg2": None, "res": res})
                        fez_alteracoes = True
                        _debug(f"[Folding] {arg1} {op} {arg2} → {resultado}")
                        continue
                    except (ZeroDivisionError, ValueError):
                        pass

                if op == "=" and c1 and res not in vars_ciclo:
                    constantes[res] = v1
                elif op == "=" and res in constantes:
                    del constantes[res]
                elif op == "label":
                    constantes.clear()  # fronteira de função — invalida todas as constantes

                novos.append(q)

            self.quadruplos = novos

        return self.quadruplos

    # -----------------------------------------------------------------------
    # 2. Propagação de Cópias
    # -----------------------------------------------------------------------

    def propagacao_copias(self) -> TAC:
        """
        Substitui o uso de uma variável pelo seu valor copiado (x = y → usa y diretamente),
        eliminando atribuições intermediárias desnecessárias.
        Não propaga variáveis atribuídas mais de uma vez nem variáveis de ciclo.
        """
        substituicoes: Dict[str, str] = {}
        atribuicoes: Dict[str, int] = {}
        modificadas_em_ciclos: Set[str] = set()

        for q in self.quadruplos:
            res = q.get("res")
            if res:
                atribuicoes[res] = atribuicoes.get(res, 0) + 1
            if q["op"] in {"goto", "ifFalse", "label"} and res:
                modificadas_em_ciclos.add(res)

        resultado = []
        for q in self.quadruplos:
            op   = q["op"]
            arg1 = q.get("arg1")
            arg2 = q.get("arg2")
            res  = q.get("res")

            if isinstance(arg1, str) and arg1 in substituicoes:
                q = dict(q); q["arg1"] = substituicoes[arg1]; arg1 = q["arg1"]
            if isinstance(arg2, str) and arg2 in substituicoes:
                q = dict(q); q["arg2"] = substituicoes[arg2]; arg2 = q["arg2"]

            if op == "=" and arg1 and res:
                if atribuicoes.get(res, 0) == 1 and res not in modificadas_em_ciclos:
                    substituicoes[res] = substituicoes.get(arg1, arg1) if isinstance(arg1, str) else arg1
                    _debug(f"[Cópia] {res} ← {arg1}")
                else:
                    substituicoes.pop(res, None)
            elif res and res in substituicoes:
                substituicoes.pop(res, None)

            resultado.append(q)

        self.quadruplos = resultado
        return self.quadruplos

    # -----------------------------------------------------------------------
    # 3. Eliminação de Subexpressões Comuns (CSE)
    # -----------------------------------------------------------------------

    def eliminar_subexpressoes_comuns(self) -> TAC:
        """
        Reutiliza o resultado de uma expressão já calculada com os mesmos
        operandos e versões de variáveis, evitando recalcular.
        Normaliza operações comutativas (a+b == b+a) para maior cobertura.
        """
        ops_binarias = {"+", "-", "*", "/", "%", "==", "!=", "<", "<=", ">", ">="}
        expressoes_vistas: Dict[Tuple, str] = {}
        versao_vars: Dict[str, int] = {}
        resultado = []

        def normalizar(op, a1, a2):
            if op in {"+", "*", "==", "!="} and a1 and a2:
                return (op, *sorted([str(a1), str(a2)]))
            return (op, a1, a2)

        def chave(op, a1, a2):
            expr = normalizar(op, a1, a2)
            v1 = versao_vars.get(expr[1], 0) if isinstance(expr[1], str) else 0
            v2 = versao_vars.get(expr[2], 0) if isinstance(expr[2], str) else 0 if len(expr) > 2 else 0
            return (*expr, v1, v2)

        for q in self.quadruplos:
            op   = q["op"]
            arg1 = q.get("arg1")
            arg2 = q.get("arg2")
            res  = q.get("res")

            if op in ops_binarias and res:
                k = chave(op, arg1, arg2)
                if k in expressoes_vistas:
                    _debug(f"[CSE] {arg1} {op} {arg2} → reutiliza {expressoes_vistas[k]}")
                    resultado.append({"op": "=", "arg1": expressoes_vistas[k], "arg2": None, "res": res})
                else:
                    expressoes_vistas[k] = res
                    resultado.append(q)
            else:
                resultado.append(q)

            if res and isinstance(res, str):
                versao_vars[res] = versao_vars.get(res, 0) + 1

        self.quadruplos = resultado
        return self.quadruplos

    # -----------------------------------------------------------------------
    # 4. Loop-Invariant Code Motion (LICM)
    # -----------------------------------------------------------------------

    def mover_invariantes(self) -> TAC:
        """
        Move para antes do ciclo as instruções cujos operandos não são
        modificados dentro desse ciclo (invariantes de ciclo).
        Usa deteção de back-edges para identificar os ciclos.
        """
        label_idx: Dict[str, int] = {
            q["res"]: i
            for i, q in enumerate(self.quadruplos)
            if q["op"] == "label" and isinstance(q.get("res"), str)
        }

        ops_com_efeitos = {
            "call", "call_void", "return", "halt",
            "write", "writec", "writev", "writes",
            "alloc", "[]=", "goto", "ifFalse", "label", "param"
        }

        invariantes: List[Tuple[int, int, Quadrupla]] = []

        for i, q in enumerate(self.quadruplos):
            if q["op"] not in {"goto", "ifFalse"}:
                continue
            target = q.get("res")
            if not isinstance(target, str) or target not in label_idx:
                continue
            start, end = label_idx[target], i
            if start >= end:
                continue

            # Variáveis definidas no ciclo — os seus usos não são invariantes
            defs: Set[str] = {
                r["res"]
                for r in self.quadruplos[start:end + 1]
                if isinstance(r.get("res"), str)
            }

            for j in range(start, end):
                instr = self.quadruplos[j]
                if instr["op"] in ops_com_efeitos:
                    continue
                args = [a for a in (instr.get("arg1"), instr.get("arg2")) if isinstance(a, str)]
                if all(a not in defs for a in args):
                    invariantes.append((start, j, instr))
                    _debug(f"[LICM] Invariante: {instr}")

        # Remove as invariantes do corpo (de trás para a frente para preservar índices)
        for _, j, _ in sorted(invariantes, key=lambda x: x[1], reverse=True):
            self.quadruplos.pop(j)

        # Insere antes do label de início do ciclo
        grupos: Dict[int, List[Quadrupla]] = defaultdict(list)
        for start, _, instr in invariantes:
            grupos[start].append(instr)

        for start, instrs in grupos.items():
            for offset, instr in enumerate(instrs):
                self.quadruplos.insert(start + offset, instr)

        return self.quadruplos

    # -----------------------------------------------------------------------
    # 5. Eliminação de Código Inatingível
    # -----------------------------------------------------------------------

    def _identificar_lideres(self) -> Set[int]:
        """
        Identifica os índices líderes de blocos básicos:
        a primeira instrução, alvos de saltos e instruções após saltos.
        """
        lideres: Set[int] = {0}
        temp_labels: Dict[str, int] = {}

        for i, q in enumerate(self.quadruplos):
            if q["op"] == "label" and q.get("res"):
                temp_labels[q["res"]] = i

        for i, q in enumerate(self.quadruplos):
            if q["op"] in {"goto", "ifFalse"}:
                target = q.get("res")
                if target and target in temp_labels:
                    lideres.add(temp_labels[target])
            if q["op"] in {"goto", "ifFalse", "return", "halt"}:
                if i + 1 < len(self.quadruplos):
                    lideres.add(i + 1)

        return lideres

    def _construir_blocos(self, lideres: Set[int]) -> List[BlocoBasico]:
        """Agrupa as quádruplas em blocos básicos com base nos líderes."""
        self.blocos.clear()
        self.mapa_idx_lider_para_id_bloco.clear()

        lideres_ord = sorted(lideres)
        for idx, inicio in enumerate(lideres_ord):
            bloco = BlocoBasico(idx, inicio)
            fim = lideres_ord[idx + 1] - 1 if idx + 1 < len(lideres_ord) else len(self.quadruplos) - 1
            bloco.fim_idx = fim
            bloco.quadruplas = self.quadruplos[inicio:fim + 1]
            self.blocos.append(bloco)
            self.mapa_idx_lider_para_id_bloco[inicio] = idx

        return self.blocos

    def _construir_cfg(self):
        """Liga cada bloco aos seus sucessores com base na última instrução."""
        self.mapa_labels_para_id_bloco.clear()
        for bloco in self.blocos:
            if bloco.quadruplas and bloco.quadruplas[0]["op"] == "label":
                label = bloco.quadruplas[0].get("res")
                if label:
                    self.mapa_labels_para_id_bloco[label] = bloco.id_bloco

        for bloco in self.blocos:
            bloco.sucessores.clear()
            if not bloco.quadruplas:
                continue

            ultima = bloco.quadruplas[-1]
            op     = ultima["op"]
            target = ultima.get("res")

            if op == "goto":
                if target and target in self.mapa_labels_para_id_bloco:
                    bloco.sucessores.append(self.mapa_labels_para_id_bloco[target])
            elif op == "ifFalse":
                if target and target in self.mapa_labels_para_id_bloco:
                    bloco.sucessores.append(self.mapa_labels_para_id_bloco[target])
                prox = bloco.fim_idx + 1
                if prox < len(self.quadruplos) and prox in self.mapa_idx_lider_para_id_bloco:
                    succ = self.mapa_idx_lider_para_id_bloco[prox]
                    if succ not in bloco.sucessores:
                        bloco.sucessores.append(succ)
            elif op not in {"return", "halt"}:
                prox = bloco.fim_idx + 1
                if prox < len(self.quadruplos) and prox in self.mapa_idx_lider_para_id_bloco:
                    bloco.sucessores.append(self.mapa_idx_lider_para_id_bloco[prox])

    def _bfs_alcancaveis(self, entrada: int = 0) -> Set[int]:
        """Percorre o CFG em largura a partir do bloco de entrada."""
        visitados: Set[int] = set()
        fila = [entrada]
        visitados.add(entrada)

        while fila:
            atual = fila.pop(0)
            bloco = next((b for b in self.blocos if b.id_bloco == atual), None)
            if bloco is None:
                continue
            for succ in bloco.sucessores:
                if succ not in visitados:
                    visitados.add(succ)
                    fila.append(succ)

        return visitados

    def eliminar_codigo_inatingivel(self) -> TAC:
        """
        Constrói o CFG e remove os blocos que não são alcançáveis a partir
        do bloco de entrada. Saltos para blocos eliminados são também descartados.
        """
        if not self.quadruplos:
            return []

        lideres     = self._identificar_lideres()
        self._construir_blocos(lideres)
        self._construir_cfg()
        alcancaveis = self._bfs_alcancaveis(0)

        labels_alcancaveis: Set[str] = set()
        for bloco in self.blocos:
            if bloco.id_bloco in alcancaveis and bloco.quadruplas:
                if bloco.quadruplas[0]["op"] == "label":
                    lbl = bloco.quadruplas[0].get("res")
                    if lbl:
                        labels_alcancaveis.add(lbl)

        tac_otimizado: TAC = []
        for bloco in sorted(self.blocos, key=lambda b: b.inicio_idx):
            if bloco.id_bloco not in alcancaveis:
                continue
            for q in bloco.quadruplas:
                if q["op"] in {"goto", "ifFalse"}:
                    if q.get("res") in labels_alcancaveis:
                        tac_otimizado.append(q)
                else:
                    tac_otimizado.append(q)

        self.quadruplos = tac_otimizado
        _debug(f"[Inatingível] {sum(len(b.quadruplas) for b in self.blocos)} → {len(tac_otimizado)} quádruplas")
        return self.quadruplos

    # -----------------------------------------------------------------------
    # 6. Eliminação de Código Morto
    # -----------------------------------------------------------------------

    def eliminar_codigo_morto(self) -> TAC:
        """
        Remove instruções cujo resultado nunca é usado (liveness analysis).
        Percorre o TAC de trás para a frente: uma variável torna-se viva
        quando é lida, e morta quando é escrita sem ter sido lida antes.

        Variáveis de ciclo são sempre tratadas como vivas — o seu valor é
        necessário nas iterações seguintes mesmo que não sejam usadas após
        o ciclo. Instruções com efeitos colaterais (I/O, chamadas, saltos)
        são sempre preservadas.
        """
        ops_com_efeitos: Set[str] = {
            "call", "call_void", "return", "halt",
            "write", "writec", "writev", "writes",
            "goto", "ifFalse", "label", "alloc", "[]=", "param"
        }

        vars_ciclo = _detectar_variaveis_de_ciclo(self.quadruplos)
        vivas: Set[str] = set(vars_ciclo)
        mantidos: TAC = []

        for q in reversed(self.quadruplos):
            op   = q["op"]
            res  = q.get("res")
            arg1 = q.get("arg1")
            arg2 = q.get("arg2")

            if (op in ops_com_efeitos
                    or (res and res in vivas)
                    or (res and res in self.variaveis_utilizador)
                    or not res):
                mantidos.append(q)
                if isinstance(arg1, str):
                    vivas.add(arg1)
                if isinstance(arg2, str):
                    vivas.add(arg2)
            else:
                _debug(f"[Morto] Eliminado: {q}")

        self.quadruplos = list(reversed(mantidos))
        return self.quadruplos


# ---------------------------------------------------------------------------
# Interface pública
# ---------------------------------------------------------------------------

def optimizar_completo(quadruplos: TAC, variaveis_utilizador: Optional[Set[str]] = None) -> TAC:
    """Ponto de entrada do otimizador. Aplica todas as técnicas e devolve o TAC otimizado."""
    return MOCPCodeOptimiser(quadruplos, variaveis_utilizador).optimise()
