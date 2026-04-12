#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
backward_chain.py - Prolog-like Interpreter (SLD-Resolution) cho Futoshiki.

ĐÁP ỨNG 2 VAI TRÒ CHÍNH:
1. QUERY TỪNG Ô: Dùng Horn Clause 'Val(R, C, V)' để truy vấn giá trị hợp lệ của 1 ô (REPL).
2. SOLVE TOÀN BÀN CỜ: Dùng Horn Clause 'solve(State, FinalState)' để giải toàn bộ bàn cờ,
   có tối ưu hóa trạng thái (bỏ Frozenset, dùng dict copy) để tránh quá tải Garbage Collection.
"""

from dataclasses import dataclass
import re
import time
from futoshiki import build_initial_assignment, compute_domain

# ==========================================
# 1. CORE UNIFICATION & SLD ENGINE 
# ==========================================
@dataclass(frozen=True)
class Var:
    name: str
    def __repr__(self): return f"?{self.name}"

@dataclass(frozen=True)
class Rule:
    head: tuple
    body: tuple

def lit(name, *args):
    return name, tuple(args)

def _walk(term, subst):
    while isinstance(term, Var) and term in subst:
        term = subst[term]
    return term

def _occurs_check(var, term, subst):
    term = _walk(term, subst)
    if var == term: return True
    if isinstance(term, tuple):
        return any(_occurs_check(var, t, subst) for t in term)
    return False

def _unify(x, y, subst):
    x = _walk(x, subst)
    y = _walk(y, subst)
    
    # Tối ưu: Nếu là dictionary (State), so sánh bằng reference hoặc value
    if type(x) is dict and type(y) is dict:
        return subst if x == y else None
        
    if x == y: return subst
    if isinstance(x, Var):
        if _occurs_check(x, y, subst): return None
        return {**subst, x: y}
    if isinstance(y, Var):
        if _occurs_check(y, x, subst): return None
        return {**subst, y: x}
    if isinstance(x, tuple) and isinstance(y, tuple) and len(x) == len(y):
        theta = subst
        for xi, yi in zip(x, y):
            theta = _unify(xi, yi, theta)
            if theta is None: return None
        return theta
    return None

def _substitute(term, subst):
    term = _walk(term, subst)
    if isinstance(term, tuple):
        return tuple(_substitute(t, subst) for t in term)
    return term

class PrologEngine:
    def __init__(self):
        self.rules = []
        self.builtins = {}
        self._fresh_id = 0
        self.nodes_explored = 0

    def add_fact(self, fact_lit):
        self.rules.append(Rule(head=fact_lit, body=()))

    def add_rule(self, head, body):
        self.rules.append(Rule(head=head, body=body))

    def ask(self, query):
        yield from self._solve_and([query], {})

    def _standardize_apart(self, rule):
        mapping = {}
        def rename(term):
            if isinstance(term, Var):
                if term not in mapping:
                    self._fresh_id += 1
                    mapping[term] = Var(f"{term.name}_{self._fresh_id}")
                return mapping[term]
            if isinstance(term, tuple):
                return tuple(rename(t) for t in term)
            return term
        return Rule(rename(rule.head), tuple(rename(g) for g in rule.body))

    def _solve_and(self, goals, subst):
        if not goals:
            yield subst
            return
        
        first_name, first_args = goals[0]
        first_args = _substitute(first_args, subst)
        rest = goals[1:]

        # Xử lý Built-in
        if first_name in self.builtins:
            for theta in self.builtins[first_name](first_args, subst):
                yield from self._solve_and(rest, theta)
            return

        # Xử lý Horn Clauses thông thường
        for rule in self.rules:
            if rule.head[0] != first_name or len(rule.head[1]) != len(first_args):
                continue
            rule_std = self._standardize_apart(rule)
            theta = _unify(rule_std.head[1], first_args, subst)
            if theta is not None:
                new_goals = list(rule_std.body) + rest
                yield from self._solve_and(new_goals, theta)


# ==========================================
# 2. FUTOSHIKI KNOWLEDGE BASE (LUẬT TRÒ CHƠI)
# ==========================================
class FutoshikiKB(PrologEngine):
    def __init__(self, puzzle, step_callback=None):
        super().__init__()
        self.puzzle = puzzle
        self.N = puzzle.N
        self.step_callback = step_callback
        self.step_count = 0
        
        self._load_facts()
        self._load_rules()
        self._load_builtins()

    def _load_facts(self):
        """Tri thức ban đầu từ lưới Sudoku/Futoshiki"""
        for i in range(1, self.N + 1):
            self.add_fact(lit("domain", i))
            
        for r in range(self.N):
            for c in range(self.N):
                val = self.puzzle.grid[r][c]
                if val != 0:
                    self.add_fact(lit("given", r, c, val))

    def _load_rules(self):
        """
        ĐỊNH NGHĨA HORN CLAUSES CHO 2 VAI TRÒ
        """
        R, C, V = Var("R"), Var("C"), Var("V")
        S, S1, SF = Var("S"), Var("S1"), Var("SF")

        # ---------------------------------------------------------
        # VAI TRÒ 1: QUERY (Val) - Dùng cho REPL tương tác
        # ---------------------------------------------------------
        # Luật 1.1: Trùng ô cho sẵn
        self.add_rule(head=lit("Val", R, C, V), body=(lit("given", R, C, V),))
        
        # Luật 1.2: Ô trống -> Lấy domain -> Check an toàn
        self.add_rule(
            head=lit("Val", R, C, V),
            body=(lit("empty", R, C), lit("domain", V), lit("safe_cell", R, C, V))
        )

        # ---------------------------------------------------------
        # VAI TRÒ 2: SOLVE (solve_board) - Giải nguyên bàn cờ
        # ---------------------------------------------------------
        # Luật 2.1: Cơ sở (Base case) - Bàn cờ đã hoàn thành
        self.add_rule(head=lit("solve_board", S, S), body=(lit("complete", S),))
        
        # Luật 2.2: Đệ quy - Chọn ô trống -> Lấy giá trị -> Gán (sinh State mới) -> Giải tiếp
        self.add_rule(
            head=lit("solve_board", S, SF),
            body=(
                lit("select_unassigned", S, R, C),
                lit("domain_val", S, R, C, V),
                lit("assign", S, R, C, V, S1),
                lit("solve_board", S1, SF)
            )
        )

    def _load_builtins(self):
        self.builtins["empty"] = self._builtin_empty
        self.builtins["safe_cell"] = self._builtin_safe_cell
        self.builtins["complete"] = self._builtin_complete
        self.builtins["select_unassigned"] = self._builtin_select_unassigned
        self.builtins["domain_val"] = self._builtin_domain_val
        self.builtins["assign"] = self._builtin_assign

    # ================== CÁC HÀM XỬ LÝ BUILT-IN ==================

    def _builtin_empty(self, args, subst):
        R, C = _walk(args[0], subst), _walk(args[1], subst)
        if isinstance(R, int) and isinstance(C, int) and self.puzzle.grid[R][C] == 0:
            yield subst

    def _builtin_safe_cell(self, args, subst):
        R, C, V = _walk(args[0], subst), _walk(args[1], subst), _walk(args[2], subst)
        if isinstance(R, int) and isinstance(C, int) and isinstance(V, int):
            init_assign = {(r, c): self.puzzle.grid[r][c] 
                           for r in range(self.N) for c in range(self.N) if self.puzzle.grid[r][c] != 0}
            if V in compute_domain(self.puzzle, init_assign, R, C):
                yield subst

    def _builtin_complete(self, args, subst):
        S = _walk(args[0], subst)
        if isinstance(S, dict) and len(S) == self.N * self.N:
            yield subst

    def _builtin_select_unassigned(self, args, subst):
        """Chọn ô theo MRV để tăng tốc Solve"""
        S = _walk(args[0], subst)
        if not isinstance(S, dict): return
        
        best_cell, best_size = None, float("inf")
        for r in range(self.N):
            for c in range(self.N):
                if (r, c) not in S:
                    dom = compute_domain(self.puzzle, S, r, c)
                    size = len(dom)
                    if size == 0: return # Dead-end
                    if size < best_size:
                        best_size, best_cell = size, (r, c)
                        if best_size == 1: break
            if best_size == 1: break
            
        if best_cell:
            r, c = best_cell
            theta = _unify(args[1], r, subst)
            if theta is not None:
                theta = _unify(args[2], c, theta)
                if theta is not None: yield theta

    def _builtin_domain_val(self, args, subst):
        S, R, C = _walk(args[0], subst), _walk(args[1], subst), _walk(args[2], subst)
        if isinstance(S, dict) and isinstance(R, int) and isinstance(C, int):
            domain = sorted(compute_domain(self.puzzle, S, R, C))
            for val in domain:
                theta = _unify(args[3], val, subst)
                if theta is not None:
                    yield theta

    def _builtin_assign(self, args, subst):
        """Tạo State mới bằng shallow copy của dict thay vì Frozenset"""
        S, R, C, V = _walk(args[0], subst), _walk(args[1], subst), _walk(args[2], subst), _walk(args[3], subst)
        if isinstance(S, dict) and isinstance(R, int) and isinstance(C, int) and isinstance(V, int):
            self.nodes_explored += 1
            
            # Tối ưu: Dùng dict.copy() tốn O(N) nhưng cực nhẹ cho N=9
            new_state = S.copy()
            new_state[(R, C)] = V
            
            # Kiểm tra Forward Checking nhanh
            safe = True
            for i in range(self.N):
                if (R, i) not in new_state and not compute_domain(self.puzzle, new_state, R, i): safe = False; break
                if (i, C) not in new_state and not compute_domain(self.puzzle, new_state, i, C): safe = False; break
            
            if safe:
                if self.step_callback:
                    self.step_count += 1
                    self.step_callback({
                        'type': 'assign',
                        'message': f'[BC] Gán ({R},{C}) = {V} | Explored: {self.nodes_explored}',
                        'assignment': new_state, 'cell': (R, C), 'value': V, 'step_number': self.step_count
                    })
                
                theta = _unify(args[4], new_state, subst)
                if theta is not None: yield theta


# ==========================================
# PUBLIC INTERFACE 1: SOLVE (Giải toàn cục)
# ==========================================
def solve_backward_chaining(puzzle, step_callback=None):
    """
    Hàm được gọi bởi main.py để giải toàn bộ bảng bằng Suy diễn lùi.
    """
    kb = FutoshikiKB(puzzle, step_callback)
    start_time = time.time()
    
    # Khởi tạo trạng thái ban đầu bằng dict thuần túy
    initial_state = build_initial_assignment(puzzle)
    final_state_var = Var("Final")
    
    # Kích hoạt luật solve_board
    query = lit("solve_board", initial_state, final_state_var)
    
    for theta in kb.ask(query):
        solution = _walk(final_state_var, theta)
        if isinstance(solution, dict) and puzzle.is_valid(solution):
            elapsed = time.time() - start_time
            stats = {'nodes': kb.nodes_explored, 'time': elapsed, 'algorithm': 'backward_chaining'}
            return solution, stats

    elapsed = time.time() - start_time
    return None, {'nodes': kb.nodes_explored, 'time': elapsed, 'algorithm': 'backward_chaining'}


# ==========================================
# PUBLIC INTERFACE 2: QUERY (REPL Tương tác)
# ==========================================
def demonstrate_prolog_interpreter(puzzle):
    """
    Trình diễn tính năng Query riêng lẻ của SLD Resolution.
    """
    kb = FutoshikiKB(puzzle)
    print("\n" + "="*60)
    print("🔮 BẬT CHẾ ĐỘ PROLOG INTERPRETER (BACKWARD CHAINING REPL)")
    print("="*60)
    print(f"Cơ sở tri thức (KB) đã nạp lưới {puzzle.N}x{puzzle.N}.")
    print("Cú pháp truy vấn: Val(Row, Col, ?X)  (Tọa độ tính từ 0)")
    print("Gõ 'exit' để thoát.\n")

    while True:
        try:
            query_str = input("?- ").strip()
            if query_str.lower() == 'exit': break
            if not query_str: continue
            
            match = re.match(r"Val\((\d+),\s*(\d+),\s*\?([A-Za-z_]+)\)", query_str)
            if not match:
                print("Lỗi cú pháp! Cú pháp đúng: Val(0, 1, ?X)")
                continue

            r, c, var_name = match.groups()
            r, c = int(r), int(c)

            if not (0 <= r < puzzle.N and 0 <= c < puzzle.N):
                print("Tọa độ ngoài phạm vi bàn cờ.")
                continue

            target_var = Var(var_name)
            query = lit("Val", r, c, target_var)
            
            found = False
            for theta in kb.ask(query):
                result_val = _walk(target_var, theta)
                if isinstance(result_val, int):
                    print(f"  {var_name} = {result_val}")
                    found = True
            
            if not found:
                print("  False. (Không có giá trị nào hợp lệ hoặc ô bị Wipeout)")
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Lỗi: {e}")