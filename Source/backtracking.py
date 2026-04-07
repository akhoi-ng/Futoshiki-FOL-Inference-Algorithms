#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
backtracking.py — Backtracking Solver cho Futoshiki

Thuat toan:
  1. Chon o trong bang MRV (Minimum Remaining Values)
  2. Thu tung gia tri trong domain cua o do
  3. Forward checking: dung compute_domain (co bound pruning) cho o bi anh huong
  4. Neu gap dead-end: backtrack va thu gia tri khac

Optimized vs ban goc:
  - Chi recompute domain cho o CUNG HANG va CUNG COT (dung set de tranh trung)
  - compute_domain da duoc them bound pruning (loai gia tri cuc tri)
  - Bo temp_assignment copy thua
  - MRV gon, bo filter du thua
"""

from futoshiki import build_initial_assignment, compute_domain


class BacktrackingSolver:
    """Solver su dung backtracking voi forward checking."""

    def __init__(self, puzzle, step_callback=None):
        self.puzzle = puzzle
        self.N = puzzle.N
        self.nodes_explored = 0
        self.backtracks = 0
        self.step_callback = step_callback
        self._step_count = 0

    def _notify(self, step_type, message, assignment, cell=None, value=None):
        """Goi callback neu co."""
        if not self.step_callback:
            return
        self._step_count += 1
        self.step_callback({
            'type': step_type,
            'message': message,
            'assignment': dict(assignment),
            'cell': cell,
            'value': value,
            'step_number': self._step_count,
        })

    # ================================================================
    # DOMAIN MANAGEMENT
    # ================================================================

    def compute_domains(self, assignment):
        """Tinh domain cho tat ca o trong. Truyen domains incrementally
        de cac o tinh sau duoc huong loi tu bound pruning cua o tinh truoc."""
        domains = {}
        for r in range(self.N):
            for c in range(self.N):
                if (r, c) not in assignment:
                    domains[(r, c)] = compute_domain(
                        self.puzzle, assignment, r, c, domains=domains
                    )
        return domains

    def forward_check(self, assignment, domains, var, value):
        """
        Cap nhat domains khi gan var = value.
        Dung compute_domain (co bound pruning) cho o cung hang/cot.
        Truyen domain context de bound pruning chinh xac hon
        khi o ke chua gan co inequality constraint.
        """
        r, c = var
        N = self.N

        # Tap o can recompute: cung hang HOAC cung cot (dung set, khong trung)
        affected = set()
        for col in range(N):
            if (r, col) in domains and (r, col) != var:
                affected.add((r, col))
        for row in range(N):
            if (row, c) in domains and (row, c) != var:
                affected.add((row, c))

        # Khoi tao new_domains voi cac o KHONG bi anh huong (giu nguyen domain)
        new_domains = {}
        for cell, dom in domains.items():
            if cell == var:
                continue
            if cell not in affected:
                new_domains[cell] = dom

        # Recompute affected cells, truyen domain context cho bound pruning
        for cell in affected:
            new_dom = compute_domain(
                self.puzzle, assignment, cell[0], cell[1],
                domains=new_domains
            )
            if len(new_dom) == 0:
                return None
            new_domains[cell] = new_dom

        return new_domains

    # ================================================================
    # VARIABLE SELECTION — MRV Heuristic
    # ================================================================

    def select_unassigned_variable(self, domains):
        """MRV: chon o trong co domain nho nhat."""
        if not domains:
            return None
        return min(domains, key=lambda cell: len(domains[cell]))

    # ================================================================
    # BACKTRACKING CHINH
    # ================================================================

    def backtrack(self, assignment, domains):
        """Ham de quy backtracking."""
        self.nodes_explored += 1

        if len(assignment) == self.N * self.N:
            self._notify('done', 'Tim thay loi giai!', assignment)
            return assignment

        var = self.select_unassigned_variable(domains)
        if var is None:
            return None

        for value in sorted(domains.get(var, set())):
            assignment[var] = value
            self._notify('assign', f'Thu ({var[0]},{var[1]}) = {value}', assignment, var, value)

            new_domains = self.forward_check(assignment, domains, var, value)

            if new_domains is not None:
                result = self.backtrack(assignment, new_domains)
                if result is not None:
                    return result

            del assignment[var]
            self.backtracks += 1
            self._notify('backtrack', f'Backtrack ({var[0]},{var[1]}) = {value}', assignment, var, value)

        return None

    # ================================================================
    # ENTRY POINT
    # ================================================================

    def solve(self):
        """Giai puzzle va tra ve (solution, stats)."""
        initial_assignment = build_initial_assignment(self.puzzle)
        domains = self.compute_domains(initial_assignment)
        solution = self.backtrack(initial_assignment, domains)
        stats = {
            'nodes'      : self.nodes_explored,
            'backtracks' : self.backtracks,
        }
        return solution, stats


# ================================================================
# PUBLIC INTERFACE
# ================================================================

def solve_backtracking(puzzle, step_callback=None):
    """Giai Futoshiki bang Backtracking. Tra ve (solution, stats)."""
    solver = BacktrackingSolver(puzzle, step_callback=step_callback)
    return solver.solve()