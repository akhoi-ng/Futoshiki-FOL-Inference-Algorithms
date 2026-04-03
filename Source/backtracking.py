#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
backtracking.py — Backtracking Solver cho Futoshiki

Thuat toan:
  1. Chon o trong bang MRV (Minimum Remaining Values)
  2. Thu tung gia tri trong domain cua o do
  3. Forward checking: cap nhat domains sau moi lan gan
  4. Neu gap dead-end: backtrack va thu gia tri khac

Fix so voi phien ban cu:
  - Bo is_valid() trong vong lap (forward_check da dam bao)
  - Bo is_valid() trong base case (khong can thiet)
  - Return (solution, stats) de tuong thich main.py
"""

from futoshiki import build_initial_assignment, compute_domain


class BacktrackingSolver:
    """Solver su dung backtracking voi forward checking."""

    def __init__(self, puzzle):
        self.puzzle = puzzle
        self.N = puzzle.N
        self.nodes_explored = 0
        self.backtracks = 0

    # ================================================================
    # DOMAIN MANAGEMENT
    # ================================================================

    def compute_domains(self, assignment):
        """
        Tinh domain cho tat ca o trong dua tren assignment hien tai.
        Dung compute_domain() tu futoshiki.py (ham dung chung).
        """
        domains = {}
        for r in range(self.N):
            for c in range(self.N):
                if (r, c) not in assignment:
                    domains[(r, c)] = compute_domain(self.puzzle, assignment, r, c)
        return domains

    def forward_check(self, assignment, domains, var, value):
        """
        Cap nhat domains cua cac o bi anh huong khi gan var = value.

        Lan luot loai 'value' khoi:
          - Cac o cung hang
          - Cac o cung cot
        Sau do ap dung lai inequality constraints.

        Tra ve domains moi neu hop le, None neu co dead-end.
        """
        r, c = var

        # Copy domains (khong sua truc tiep de de backtrack)
        new_domains = {cell: dom.copy() for cell, dom in domains.items() if cell != var}

        # Assignment tam thoi de tinh inequality
        temp_assignment = dict(assignment)
        temp_assignment[var] = value

        # Loai 'value' khoi cac o cung hang
        for col in range(self.N):
            if (r, col) in new_domains:
                new_domains[(r, col)] = compute_domain(
                    self.puzzle, temp_assignment, r, col
                )
                if len(new_domains[(r, col)]) == 0:
                    return None  # Dead-end

        # Loai 'value' khoi cac o cung cot
        for row in range(self.N):
            if (row, c) in new_domains:
                new_domains[(row, c)] = compute_domain(
                    self.puzzle, temp_assignment, row, c
                )
                if len(new_domains[(row, c)]) == 0:
                    return None  # Dead-end

        return new_domains

    # ================================================================
    # VARIABLE SELECTION — MRV Heuristic
    # ================================================================

    def select_unassigned_variable(self, assignment, domains):
        """
        MRV: chon o trong co domain nho nhat.
        O co it lua chon nhat → phat hien dead-end som nhat.
        """
        unassigned = [
            cell for cell in domains
            if cell not in assignment
        ]

        if not unassigned:
            return None

        return min(unassigned, key=lambda cell: len(domains.get(cell, set())))

    # ================================================================
    # BACKTRACKING CHINH
    # ================================================================

    def backtrack(self, assignment, domains):
        """
        Ham de quy backtracking.

        Fix so voi phien ban cu:
          - KHONG goi is_valid() trong vong lap
            (forward_check da dam bao moi buoc deu hop le)
          - KHONG goi is_valid() o base case
            (forward_check dam bao suot qua trinh)
        """
        self.nodes_explored += 1

        # ── Base case: da dien het ──
        if len(assignment) == self.N * self.N:
            return assignment  # forward_check da dam bao valid

        # ── Chon o tiep theo (MRV) ──
        var = self.select_unassigned_variable(assignment, domains)
        if var is None:
            return None

        # ── Thu tung gia tri trong domain ──
        for value in sorted(domains.get(var, set())):
            assignment[var] = value

            # Forward checking thay the is_valid()
            new_domains = self.forward_check(assignment, domains, var, value)

            if new_domains is not None:
                result = self.backtrack(assignment, new_domains)
                if result is not None:
                    return result

            # Backtrack
            del assignment[var]
            self.backtracks += 1

        return None

    # ================================================================
    # ENTRY POINT
    # ================================================================

    def solve(self):
        """
        Giai puzzle va tra ve (solution, stats).
        stats chua: nodes, backtracks de dung trong bao cao.
        """
        initial_assignment = build_initial_assignment(self.puzzle)
        domains = self.compute_domains(initial_assignment)

        solution = self.backtrack(initial_assignment, domains)

        stats = {
            'nodes'      : self.nodes_explored,
            'backtracks' : self.backtracks,
        }

        return solution, stats


# ================================================================
# PUBLIC INTERFACE — goi tu main.py
# ================================================================

def solve_backtracking(puzzle):
    """
    Giai Futoshiki bang Backtracking.
    Tra ve (solution, stats) de tuong thich main.py.
    """
    solver = BacktrackingSolver(puzzle)
    return solver.solve()