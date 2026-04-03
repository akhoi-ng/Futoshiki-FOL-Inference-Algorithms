#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Backtracking Algorithm cho Futoshiki Solver

Thuat toan CSP voi backtracking:
- Chon o trong (variable selection voi MRV heuristic)
- Thu tung gia tri trong domain cua o do
- Kiem tra consistency voi forward checking
- Neu valid: de quy giai tiep
- Neu fail: backtrack va thu gia tri khac
"""

import copy


class BacktrackingSolver:
    """Solver su dung backtracking voi constraint propagation."""
    
    def __init__(self, puzzle):
        self.puzzle = puzzle
        self.N = puzzle.N
        self.nodes_explored = 0
        self.backtracks = 0
    
    def compute_domains(self, assignment):
        """Tinh toan domains cho tat ca cac o trong."""
        domains = {}
        
        for r in range(self.N):
            for c in range(self.N):
                if (r, c) not in assignment:
                    domain = set(range(1, self.N + 1))
                    
                    # Loai bo gia tri da dung trong hang
                    for col in range(self.N):
                        if (r, col) in assignment:
                            domain.discard(assignment[(r, col)])
                    
                    # Loai bo gia tri da dung trong cot
                    for row in range(self.N):
                        if (row, c) in assignment:
                            domain.discard(assignment[(row, c)])
                    
                    domain = self._apply_inequality_constraints(r, c, domain, assignment)
                    domains[(r, c)] = domain
        
        return domains
    
    def _apply_inequality_constraints(self, r, c, domain, assignment):
        """Ap dung rang buoc bat dang thuc len domain cua o (r,c)."""
        new_domain = domain.copy()
        
        # Check constraint voi o ben trai
        if c > 0 and (r, c - 1) in assignment:
            left_val = assignment[(r, c - 1)]
            if self.puzzle.h_con[r][c - 1] == 1:
                new_domain = {v for v in new_domain if v > left_val}
            elif self.puzzle.h_con[r][c - 1] == -1:
                new_domain = {v for v in new_domain if v < left_val}
        
        # Check constraint voi o ben phai
        if c < self.N - 1 and (r, c + 1) in assignment:
            right_val = assignment[(r, c + 1)]
            if self.puzzle.h_con[r][c] == 1:
                new_domain = {v for v in new_domain if v < right_val}
            elif self.puzzle.h_con[r][c] == -1:
                new_domain = {v for v in new_domain if v > right_val}
        
        # Check constraint voi o phia tren
        if r > 0 and (r - 1, c) in assignment:
            up_val = assignment[(r - 1, c)]
            if self.puzzle.v_con[r - 1][c] == 1:
                new_domain = {v for v in new_domain if v > up_val}
            elif self.puzzle.v_con[r - 1][c] == -1:
                new_domain = {v for v in new_domain if v < up_val}
        
        # Check constraint voi o phia duoi
        if r < self.N - 1 and (r + 1, c) in assignment:
            down_val = assignment[(r + 1, c)]
            if self.puzzle.v_con[r][c] == 1:
                new_domain = {v for v in new_domain if v < down_val}
            elif self.puzzle.v_con[r][c] == -1:
                new_domain = {v for v in new_domain if v > down_val}
        
        return new_domain
    
    def select_unassigned_variable(self, assignment, domains):
        """Chon o trong tiep theo de gan gia tri (MRV heuristic)."""
        unassigned = [(r, c) for r in range(self.N) for c in range(self.N) 
                     if (r, c) not in assignment]
        
        if not unassigned:
            return None
        
        # Chon o co domain size nho nhat
        min_cell = min(unassigned, key=lambda cell: len(domains.get(cell, set())))
        return min_cell
    
    def forward_check(self, assignment, domains, var, value):
        """Forward checking: Update domains sau khi gan var = value."""
        r, c = var
        new_domains = {}
        
        for cell, domain in domains.items():
            if cell != var:
                new_domains[cell] = domain.copy()
        
        temp_assignment = assignment.copy()
        temp_assignment[var] = value
        
        # Update domains cua cac o bi anh huong
        for col in range(self.N):
            if (r, col) in new_domains:
                new_domains[(r, col)].discard(value)
                new_domains[(r, col)] = self._apply_inequality_constraints(
                    r, col, new_domains[(r, col)], temp_assignment
                )
                if len(new_domains[(r, col)]) == 0:
                    return None
        
        for row in range(self.N):
            if (row, c) in new_domains:
                new_domains[(row, c)].discard(value)
                new_domains[(row, c)] = self._apply_inequality_constraints(
                    row, c, new_domains[(row, c)], temp_assignment
                )
                if len(new_domains[(row, c)]) == 0:
                    return None
        
        return new_domains
    
    def backtrack(self, assignment, domains):
        """Ham de quy backtracking chinh."""
        self.nodes_explored += 1
        
        # Base case
        if len(assignment) == self.N * self.N:
            if self.puzzle.is_valid(assignment):
                return assignment
            else:
                return None
        
        # Chon o trong tiep theo (MRV)
        var = self.select_unassigned_variable(assignment, domains)
        if var is None:
            return None
        
        # Thu tung gia tri trong domain
        for value in sorted(domains.get(var, set())):
            assignment[var] = value
            
            if self.puzzle.is_valid(assignment):
                # Forward checking
                new_domains = self.forward_check(assignment, domains, var, value)
                
                if new_domains is not None:
                    result = self.backtrack(assignment, new_domains)
                    if result is not None:
                        return result
            
            # Backtrack
            del assignment[var]
            self.backtracks += 1
        
        return None
    
    def solve(self):
        """Entry point de giai puzzle."""
        from futoshiki import build_initial_assignment
        
        initial_assignment = build_initial_assignment(self.puzzle)
        domains = self.compute_domains(initial_assignment)
        solution = self.backtrack(initial_assignment, domains)
        
        stats = {
            'nodes': self.nodes_explored,
            'backtracks': self.backtracks
        }
        
        return solution, stats


def solve_backtracking(puzzle):
    """Giai Futoshiki puzzle bang Backtracking."""
    solver = BacktrackingSolver(puzzle)
    return solver.solve()
