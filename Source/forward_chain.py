#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
forward_chain.py — Forward Chaining Solver cho Futoshiki

Qua trinh:
  1. Khoi tao KB tu cac Given facts (A5: Given => Val)
  2. Ap dung cac FOL rules lien tuc cho den fixpoint:
       - Singleton domain  (A1 + A2)
       - Row uniqueness     (A3)
       - Col uniqueness     (A6)
       - Hidden single      (A3 + A6 ket hop)
  3. Neu FC dat fixpoint ma chua xong (puzzle kho):
       → Ket hop Backtracking de hoan tat
       → FC da thu hep domains nen BT se nhanh hon nhieu

Fix so voi phien ban cu:
  - Them fallback backtracking khi FC bi stuck
  - Tra ve (solution, stats) de tuong thich main.py
  - stats ghi ro FC inferences vs BT nodes (cho bao cao)
"""

from futoshiki import build_initial_assignment, compute_domain


# ================================================================
# KNOWLEDGE BASE
# ================================================================

class KnowledgeBase:
    """
    Luu tru facts va domains cua puzzle.

    facts  : dict {(r,c): value}  — cac o da biet gia tri
    domains: dict {(r,c): set}    — cac gia tri con kha thi
    """

    def __init__(self, puzzle, initial_assignment):
        self.puzzle = puzzle
        self.N = puzzle.N
        self.facts = dict(initial_assignment)
        self.inferences_count = 0

        # Khoi tao domains cho tat ca o trong
        self.domains = {}
        for r in range(self.N):
            for c in range(self.N):
                if (r, c) not in self.facts:
                    self.domains[(r, c)] = set(range(1, self.N + 1))

        # Cap nhat domains theo facts ban dau
        self._propagate_all_facts()

    def _propagate_all_facts(self):
        """Lan truyen tat ca facts hien co vao domains."""
        for (r, c), value in list(self.facts.items()):
            self._propagate_single_fact(r, c, value)

    def _propagate_single_fact(self, r, c, value):
        """
        Khi biet o (r,c) = value, cap nhat domains cua
        cac o bi anh huong (cung hang, cung cot, ke nhau co constraint).
        Tuong ung voi viec ap dung Axiom A3, A6, A4, A7, A8, A9.
        """
        # Loai 'value' khoi cac o cung hang (A3)
        for col in range(self.N):
            if (r, col) in self.domains:
                self.domains[(r, col)].discard(value)

        # Loai 'value' khoi cac o cung cot (A6)
        for row in range(self.N):
            if (row, c) in self.domains:
                self.domains[(row, c)].discard(value)

        # Ap dung inequality constraints tu o nay (A4, A7, A8, A9)
        self._apply_inequality_from(r, c, value)

    def _apply_inequality_from(self, r, c, value):
        """Thu hep domains cac o ke nhau co inequality constraint."""
        N = self.N

        # (r,c) < (r,c+1)  =>  (r,c+1) phai > value
        if c < N - 1 and self.puzzle.h_con[r][c] == 1:
            if (r, c + 1) in self.domains:
                self.domains[(r, c + 1)] = {
                    v for v in self.domains[(r, c + 1)] if v > value
                }

        # (r,c) > (r,c+1)  =>  (r,c+1) phai < value
        if c < N - 1 and self.puzzle.h_con[r][c] == -1:
            if (r, c + 1) in self.domains:
                self.domains[(r, c + 1)] = {
                    v for v in self.domains[(r, c + 1)] if v < value
                }

        # (r,c-1) < (r,c)  =>  (r,c-1) phai < value
        if c > 0 and self.puzzle.h_con[r][c - 1] == 1:
            if (r, c - 1) in self.domains:
                self.domains[(r, c - 1)] = {
                    v for v in self.domains[(r, c - 1)] if v < value
                }

        # (r,c-1) > (r,c)  =>  (r,c-1) phai > value
        if c > 0 and self.puzzle.h_con[r][c - 1] == -1:
            if (r, c - 1) in self.domains:
                self.domains[(r, c - 1)] = {
                    v for v in self.domains[(r, c - 1)] if v > value
                }

        # (r,c) < (r+1,c)  =>  (r+1,c) phai > value
        if r < N - 1 and self.puzzle.v_con[r][c] == 1:
            if (r + 1, c) in self.domains:
                self.domains[(r + 1, c)] = {
                    v for v in self.domains[(r + 1, c)] if v > value
                }

        # (r,c) > (r+1,c)  =>  (r+1,c) phai < value
        if r < N - 1 and self.puzzle.v_con[r][c] == -1:
            if (r + 1, c) in self.domains:
                self.domains[(r + 1, c)] = {
                    v for v in self.domains[(r + 1, c)] if v < value
                }

        # (r-1,c) < (r,c)  =>  (r-1,c) phai < value
        if r > 0 and self.puzzle.v_con[r - 1][c] == 1:
            if (r - 1, c) in self.domains:
                self.domains[(r - 1, c)] = {
                    v for v in self.domains[(r - 1, c)] if v < value
                }

        # (r-1,c) > (r,c)  =>  (r-1,c) phai > value
        if r > 0 and self.puzzle.v_con[r - 1][c] == -1:
            if (r - 1, c) in self.domains:
                self.domains[(r - 1, c)] = {
                    v for v in self.domains[(r - 1, c)] if v > value
                }

    def add_fact(self, r, c, value):
        """
        Them fact moi Val(r,c,value) vao KB.
        Tra ve True neu thanh cong, False neu da biet roi.
        """
        if (r, c) in self.facts:
            return False

        self.facts[(r, c)] = value
        self.inferences_count += 1

        if (r, c) in self.domains:
            del self.domains[(r, c)]

        self._propagate_single_fact(r, c, value)
        return True

    def is_complete(self):
        return len(self.facts) == self.N * self.N

    def is_consistent(self):
        """Kiem tra co o nao domain rong khong."""
        return all(len(d) > 0 for d in self.domains.values())

    def get_inferred_count(self):
        return self.inferences_count


# ================================================================
# FOL RULES — ap dung tung buoc
# ================================================================

def apply_singleton_domain_rule(kb):
    """
    Rule: neu domain cua o chi con 1 gia tri → gan ngay.
    Tuong ung: A1 (moi o co it nhat 1 gia tri) + A2 (nhieu nhat 1).
    """
    count = 0
    changed = True

    while changed:
        changed = False
        for (r, c), domain in list(kb.domains.items()):
            if len(domain) == 1:
                value = next(iter(domain))
                if kb.add_fact(r, c, value):
                    count += 1
                    changed = True
                    break  # restart vi domains da thay doi
            elif len(domain) == 0:
                return count  # Dead-end

    return count


def apply_row_uniqueness_rule(kb):
    """
    Rule: neu hang co N-1 o da dien → o con lai = gia tri chua co.
    Tuong ung Axiom A3 (row uniqueness).
    """
    count = 0
    N = kb.N

    for r in range(N):
        # Tim o trong trong hang
        empty_cells = [(r, c) for c in range(N) if (r, c) not in kb.facts]

        if len(empty_cells) == 1:
            (er, ec) = empty_cells[0]
            used = {kb.facts[(r, c)] for c in range(N) if (r, c) in kb.facts}
            missing = set(range(1, N + 1)) - used

            if len(missing) == 1:
                value = next(iter(missing))
                if (er, ec) in kb.domains and value in kb.domains[(er, ec)]:
                    if kb.add_fact(er, ec, value):
                        count += 1

    return count


def apply_col_uniqueness_rule(kb):
    """
    Rule: neu cot co N-1 o da dien → o con lai = gia tri chua co.
    Tuong ung Axiom A6 (column uniqueness).
    """
    count = 0
    N = kb.N

    for c in range(N):
        empty_cells = [(r, c) for r in range(N) if (r, c) not in kb.facts]

        if len(empty_cells) == 1:
            (er, ec) = empty_cells[0]
            used = {kb.facts[(r, c)] for r in range(N) if (r, c) in kb.facts}
            missing = set(range(1, N + 1)) - used

            if len(missing) == 1:
                value = next(iter(missing))
                if (er, ec) in kb.domains and value in kb.domains[(er, ec)]:
                    if kb.add_fact(er, ec, value):
                        count += 1

    return count


def apply_hidden_single_rule(kb):
    """
    Rule: neu trong hang/cot chi co 1 o co the nhan gia tri v → gan v.
    Tuong ung A3 + A6 ket hop: neu moi gia tri phai xuat hien dung 1 lan,
    o nao la duy nhat co the chua v thi buoc phai la v.
    """
    count = 0
    N = kb.N

    # Kiem tra theo hang
    for r in range(N):
        for value in range(1, N + 1):
            # Gia tri nay da co trong hang chua?
            if any((r, c) in kb.facts and kb.facts[(r, c)] == value
                   for c in range(N)):
                continue

            # Tim cac o trong hang co the la 'value'
            possible = [
                (r, c) for c in range(N)
                if (r, c) in kb.domains and value in kb.domains[(r, c)]
            ]

            if len(possible) == 1:
                er, ec = possible[0]
                if kb.add_fact(er, ec, value):
                    count += 1
                    return count  # restart vong lap ngoai

    # Kiem tra theo cot
    for c in range(N):
        for value in range(1, N + 1):
            if any((r, c) in kb.facts and kb.facts[(r, c)] == value
                   for r in range(N)):
                continue

            possible = [
                (r, c) for r in range(N)
                if (r, c) in kb.domains and value in kb.domains[(r, c)]
            ]

            if len(possible) == 1:
                er, ec = possible[0]
                if kb.add_fact(er, ec, value):
                    count += 1
                    return count

    return count


# ================================================================
# FORWARD CHAINING SOLVER CHINH
# ================================================================

def solve_forward_chaining(puzzle):
    """
    Giai Futoshiki bang Forward Chaining.

    Qua trinh:
      Buoc 1: FC chay den fixpoint (ap dung tat ca rules)
      Buoc 2: Neu FC chua xong → Backtracking hoan tat
              (FC da thu hep domains nen BT se nhanh hon nhieu)

    Tra ve (solution, stats) de tuong thich main.py.
    stats phan biet ro FC vs BT de viet bao cao.
    """
    initial_assignment = build_initial_assignment(puzzle)
    kb = KnowledgeBase(puzzle, initial_assignment)

    iterations = 0
    max_iterations = 1000  # tranh loop vo han

    # ── Buoc 1: Forward Chaining den fixpoint ──
    while not kb.is_complete() and iterations < max_iterations:
        iterations += 1
        new_facts = 0

        new_facts += apply_singleton_domain_rule(kb)
        if not kb.is_consistent():
            return None, _make_stats(iterations, kb, 0, 0, fc_solved=False)

        new_facts += apply_row_uniqueness_rule(kb)
        if not kb.is_consistent():
            return None, _make_stats(iterations, kb, 0, 0, fc_solved=False)

        new_facts += apply_col_uniqueness_rule(kb)
        if not kb.is_consistent():
            return None, _make_stats(iterations, kb, 0, 0, fc_solved=False)

        new_facts += apply_hidden_single_rule(kb)
        if not kb.is_consistent():
            return None, _make_stats(iterations, kb, 0, 0, fc_solved=False)

        # Fixpoint: khong suy duoc them gi → dung FC
        if new_facts == 0:
            break

    # ── Ket qua FC ──
    if kb.is_complete():
        # FC giai duoc hoan toan
        if puzzle.is_valid(kb.facts):
            return kb.facts, _make_stats(iterations, kb, 0, 0, fc_solved=True)
        else:
            return None, _make_stats(iterations, kb, 0, 0, fc_solved=False)

    # ── Buoc 2: FC bi stuck → dung Backtracking hoan tat ──
    # Tan dung facts va domains da thu hep boi FC
    from backtracking import BacktrackingSolver

    bt_solver = BacktrackingSolver(puzzle)

    # Dung lai facts tu FC lam diem bat dau cho BT
    partial = dict(kb.facts)

    # Tinh lai domains tu partial assignment (da duoc thu hep boi FC)
    domains = {}
    for (r, c), domain in kb.domains.items():
        # Dung domain da thu hep boi FC (khong tinh lai tu dau)
        if len(domain) > 0:
            domains[(r, c)] = domain.copy()
        else:
            # Dead-end
            return None, _make_stats(iterations, kb, 0, 0, fc_solved=False)

    result = bt_solver.backtrack(partial, domains)

    return result, _make_stats(
        iterations, kb,
        bt_solver.nodes_explored,
        bt_solver.backtracks,
        fc_solved=False
    )


def _make_stats(iterations, kb, bt_nodes, bt_backtracks, fc_solved):
    """Tao dict thong ke cho bao cao."""
    return {
        'iterations'  : iterations,
        'inferences'  : kb.get_inferred_count(),
        'nodes'       : kb.get_inferred_count() + bt_nodes,
        'backtracks'  : bt_backtracks,
        'fc_solved'   : fc_solved,   # True = FC giai duoc, False = can BT ho tro
    }