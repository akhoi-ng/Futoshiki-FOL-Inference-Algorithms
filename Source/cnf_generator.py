#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cnf_generator.py — FOL to CNF / Ground KB Generator cho Futoshiki
CSC14003 - Co so Tri tue Nhan tao

Module nay thuc hien:
  1. Bieu dien cac FOL axioms (A1–A9) cho Futoshiki
  2. Ground cac axiom — thay bien luong tu (∀i, ∀j, ...) bang gia tri cu the {1..N}
  3. Chuyen sang CNF (Conjunctive Normal Form) — moi axiom → tap cac clause
  4. Giai bang SAT solver (pysat Glucose4) de tim loi giai

Cach dung:
  python main.py Inputs/input-01.txt cnf
  python main.py Inputs/input-01.txt cnf Outputs/output-01.txt

Axiom Reference (tu de bai):
  A1: Moi o co it nhat 1 gia tri       ∀i ∀j ∃v Val(i,j,v)
  A2: Moi o co nhieu nhat 1 gia tri    ∀i ∀j ∀v1 ∀v2 (Val(i,j,v1) ∧ Val(i,j,v2)) ⇒ v1=v2
  A3: Hang duy nhat                    ∀i ∀j1 ∀j2 ∀v (Val(i,j1,v) ∧ Val(i,j2,v) ∧ j1≠j2) ⇒ ⊥
  A4: Rang buoc ngang < (LessH)        (LessH(i,j) ∧ Val(i,j,v1) ∧ Val(i,j+1,v2)) ⇒ v1<v2
  A5: Given clue bat buoc              Given(i,j,v) ⇒ Val(i,j,v)
  A6: Cot duy nhat                     (tuong tu A3 cho cot)
  A7: Rang buoc ngang > (GreaterH)     (tuong tu A4 cho >)
  A8: Rang buoc doc < (LessV)          (tuong tu A4 cho vertical)
  A9: Rang buoc doc > (GreaterV)       (tuong tu A7 cho vertical)
"""

import time
import os
from itertools import combinations

from futoshiki import build_initial_assignment


# ================================================================
# VARIABLE ENCODING
# ================================================================
# Moi bien propositional tuong ung voi 1 menh de Val(r, c, v):
#   "O (r, c) duoc gan gia tri v"
#
# Anh xa: Val(r, c, v) → integer ID duong (1..N³)
#   ID = r * N² + c * N + (v - 1) + 1
#
# Trong do:
#   r, c: 0-based index (0..N-1) — khop voi code hien tai
#   v:    1-based value  (1..N)  — khop voi de bai
#
# Vi du voi N=4:
#   Val(0,0,1) → 1,  Val(0,0,2) → 2, ..., Val(0,0,4) → 4
#   Val(0,1,1) → 5,  Val(0,1,2) → 6, ...
#   Val(3,3,4) → 64 = 4³
# ================================================================

def var_id(r, c, v, N):
    """
    Anh xa Val(r, c, v) → integer ID cho SAT solver.

    Parameters:
        r (int): chi so hang, 0-based (0..N-1)
        c (int): chi so cot, 0-based (0..N-1)
        v (int): gia tri, 1-based (1..N)
        N (int): kich thuoc puzzle

    Returns:
        int: ID duong (1..N³), dung lam bien trong DIMACS/pysat
    """
    return r * N * N + c * N + (v - 1) + 1


def decode_var(vid, N):
    """
    Giai ma variable ID → (r, c, v).

    Parameters:
        vid (int): ID duong (1..N³)
        N (int):   kich thuoc puzzle

    Returns:
        tuple: (r, c, v) voi r,c 0-based va v 1-based
    """
    vid -= 1
    r = vid // (N * N)
    vid %= (N * N)
    c = vid // N
    v = vid % N + 1
    return r, c, v


def literal_to_str(lit, N):
    """
    Chuyen literal (int) thanh chuoi doc duoc.
    Dung de debug hoac in ra bao cao.

    Vi du: 5 → "Val(0,1,1)", -5 → "¬Val(0,1,1)"
    """
    sign = "" if lit > 0 else "¬"
    r, c, v = decode_var(abs(lit), N)
    return f"{sign}Val({r},{c},{v})"


# ================================================================
# GROUND KB GENERATION — tung axiom FOL → CNF clauses
# ================================================================
# Moi ham duoi day tuong ung voi 1 axiom trong de bai.
# Tat ca deu tra ve list[list[int]] — danh sach cac clause,
# moi clause la list cac literal (int duong = true, am = false).
#
# Quy trinh ground hoa:
#   FOL axiom (co bien luong tu ∀i, ∀j, ∀v)
#     → Thay tat ca bien bang moi gia tri cu the trong {0..N-1} hoac {1..N}
#     → Duoc tap menh de propositional (khong con bien)
#     → Chuyen sang CNF bang contrapositive / distribution
# ================================================================

def generate_at_least_one(N):
    """
    Axiom A1: Moi o phai co it nhat 1 gia tri.

    FOL goc:
        ∀i ∀j ∃v Val(i, j, v)

    Chuyen CNF:
        Voi moi (i, j), them 1 clause chua tat ca gia tri co the:
        [Val(i,j,1) ∨ Val(i,j,2) ∨ ... ∨ Val(i,j,N)]

    So clause sinh ra: N² (1 clause cho moi o)

    Vi du N=4, o (0,0):
        [Val(0,0,1), Val(0,0,2), Val(0,0,3), Val(0,0,4)]
        → "O (0,0) phai la 1 hoac 2 hoac 3 hoac 4"
    """
    clauses = []
    for r in range(N):
        for c in range(N):
            # Clause: it nhat 1 trong cac gia tri phai dung
            clause = [var_id(r, c, v, N) for v in range(1, N + 1)]
            clauses.append(clause)
    return clauses


def generate_at_most_one(N):
    """
    Axiom A2: Moi o co nhieu nhat 1 gia tri.

    FOL goc:
        ∀i ∀j ∀v1 ∀v2 (Val(i,j,v1) ∧ Val(i,j,v2)) ⇒ v1 = v2

    Contrapositive (khi v1 ≠ v2):
        ¬(Val(i,j,v1) ∧ Val(i,j,v2))
        = ¬Val(i,j,v1) ∨ ¬Val(i,j,v2)

    CNF:
        Voi moi (i,j), voi moi cap v1 < v2:
        [¬Val(i,j,v1), ¬Val(i,j,v2)]

    So clause: N² × C(N,2)

    Vi du N=4, o (0,0):
        [¬Val(0,0,1), ¬Val(0,0,2)]  → "khong the vua la 1 vua la 2"
        [¬Val(0,0,1), ¬Val(0,0,3)]
        ... (6 clause cho moi o)
    """
    clauses = []
    for r in range(N):
        for c in range(N):
            for v1, v2 in combinations(range(1, N + 1), 2):
                clauses.append([-var_id(r, c, v1, N), -var_id(r, c, v2, N)])
    return clauses


def generate_row_uniqueness(N):
    """
    Axiom A3: Moi gia tri xuat hien dung 1 lan trong moi hang.

    FOL goc:
        ∀i ∀j1 ∀j2 ∀v (Val(i,j1,v) ∧ Val(i,j2,v) ∧ j1≠j2) ⇒ ⊥

    Contrapositive:
        ¬Val(i,j1,v) ∨ ¬Val(i,j2,v)

    CNF:
        Voi moi hang i, gia tri v, cap cot j1 < j2:
        [¬Val(i,j1,v), ¬Val(i,j2,v)]
        → "khong the 2 o cung hang co cung gia tri"

    So clause: N × N × C(N,2)
    """
    clauses = []
    for r in range(N):
        for v in range(1, N + 1):
            for c1, c2 in combinations(range(N), 2):
                clauses.append([-var_id(r, c1, v, N), -var_id(r, c2, v, N)])
    return clauses


def generate_col_uniqueness(N):
    """
    Axiom A6: Moi gia tri xuat hien dung 1 lan trong moi cot.

    FOL goc:
        ∀j ∀i1 ∀i2 ∀v (Val(i1,j,v) ∧ Val(i2,j,v) ∧ i1≠i2) ⇒ ⊥

    CNF:
        Voi moi cot j, gia tri v, cap hang i1 < i2:
        [¬Val(i1,j,v), ¬Val(i2,j,v)]

    So clause: N × N × C(N,2)
    """
    clauses = []
    for c in range(N):
        for v in range(1, N + 1):
            for r1, r2 in combinations(range(N), 2):
                clauses.append([-var_id(r1, c, v, N), -var_id(r2, c, v, N)])
    return clauses


def generate_horizontal_less(N, puzzle):
    """
    Axiom A4: Rang buoc ngang "nho hon" (LessH).

    FOL goc:
        ∀i ∀j ∀v1 ∀v2
        (LessH(i,j) ∧ Val(i,j,v1) ∧ Val(i,j+1,v2)) ⇒ Less(v1,v2)

    Nghia la: neu o (i,j) < o (i,j+1), thi v1 phai < v2.

    Contrapositive (khi v1 ≥ v2 — vi pham):
        ¬Val(i,j,v1) ∨ ¬Val(i,j+1,v2)

    CNF:
        Voi moi (i,j) co constraint LessH,
        voi moi cap (v1, v2) ma v1 >= v2:
        [¬Val(i,j,v1), ¬Val(i,j+1,v2)]
        → "cam gan v1 cho (i,j) va v2 cho (i,j+1) neu v1 >= v2"

    Vi du: o (0,0) < o (0,1) voi N=4:
        [¬Val(0,0,2), ¬Val(0,1,1)]  → "khong the (0,0)=2 va (0,1)=1"
        [¬Val(0,0,3), ¬Val(0,1,1)]
        [¬Val(0,0,4), ¬Val(0,1,1)]
        ... (tong cong 10 clause cho moi constraint)
    """
    clauses = []
    for r in range(N):
        for c in range(N - 1):
            if puzzle.h_con[r][c] == 1:  # LessH(r, c): o(r,c) < o(r,c+1)
                for v1 in range(1, N + 1):
                    for v2 in range(1, N + 1):
                        if v1 >= v2:  # vi pham v1 < v2
                            clauses.append([
                                -var_id(r, c, v1, N),
                                -var_id(r, c + 1, v2, N)
                            ])
    return clauses


def generate_horizontal_greater(N, puzzle):
    """
    Axiom A7: Rang buoc ngang "lon hon" (GreaterH).

    FOL goc:
        ∀i ∀j ∀v1 ∀v2
        (GreaterH(i,j) ∧ Val(i,j,v1) ∧ Val(i,j+1,v2)) ⇒ Less(v2,v1)

    Nghia la: neu o (i,j) > o (i,j+1), thi v1 phai > v2.

    Contrapositive (khi v1 ≤ v2 — vi pham):
        ¬Val(i,j,v1) ∨ ¬Val(i,j+1,v2)

    CNF:
        Voi moi (i,j) co constraint GreaterH,
        voi moi cap (v1, v2) ma v1 <= v2:
        [¬Val(i,j,v1), ¬Val(i,j+1,v2)]
    """
    clauses = []
    for r in range(N):
        for c in range(N - 1):
            if puzzle.h_con[r][c] == -1:  # GreaterH(r, c): o(r,c) > o(r,c+1)
                for v1 in range(1, N + 1):
                    for v2 in range(1, N + 1):
                        if v1 <= v2:  # vi pham v1 > v2
                            clauses.append([
                                -var_id(r, c, v1, N),
                                -var_id(r, c + 1, v2, N)
                            ])
    return clauses


def generate_vertical_less(N, puzzle):
    """
    Axiom A8: Rang buoc doc "nho hon" (LessV).

    FOL goc:
        ∀i ∀j ∀v1 ∀v2
        (LessV(i,j) ∧ Val(i,j,v1) ∧ Val(i+1,j,v2)) ⇒ Less(v1,v2)

    Contrapositive (khi v1 ≥ v2):
        ¬Val(i,j,v1) ∨ ¬Val(i+1,j,v2)

    CNF:
        Voi moi (i,j) co constraint LessV,
        voi moi (v1, v2) ma v1 >= v2:
        [¬Val(i,j,v1), ¬Val(i+1,j,v2)]
    """
    clauses = []
    for r in range(N - 1):
        for c in range(N):
            if puzzle.v_con[r][c] == 1:  # LessV(r, c): o(r,c) < o(r+1,c)
                for v1 in range(1, N + 1):
                    for v2 in range(1, N + 1):
                        if v1 >= v2:  # vi pham v1 < v2
                            clauses.append([
                                -var_id(r, c, v1, N),
                                -var_id(r + 1, c, v2, N)
                            ])
    return clauses


def generate_vertical_greater(N, puzzle):
    """
    Axiom A9: Rang buoc doc "lon hon" (GreaterV).

    FOL goc:
        ∀i ∀j ∀v1 ∀v2
        (GreaterV(i,j) ∧ Val(i,j,v1) ∧ Val(i+1,j,v2)) ⇒ Less(v2,v1)

    Contrapositive (khi v1 ≤ v2):
        ¬Val(i,j,v1) ∨ ¬Val(i+1,j,v2)

    CNF:
        Voi moi (i,j) co constraint GreaterV,
        voi moi (v1, v2) ma v1 <= v2:
        [¬Val(i,j,v1), ¬Val(i+1,j,v2)]
    """
    clauses = []
    for r in range(N - 1):
        for c in range(N):
            if puzzle.v_con[r][c] == -1:  # GreaterV(r,c): o(r,c) > o(r+1,c)
                for v1 in range(1, N + 1):
                    for v2 in range(1, N + 1):
                        if v1 <= v2:  # vi pham v1 > v2
                            clauses.append([
                                -var_id(r, c, v1, N),
                                -var_id(r + 1, c, v2, N)
                            ])
    return clauses


def generate_given_clues(N, puzzle):
    """
    Axiom A5: Cac o da cho (Given) phai giu nguyen gia tri.

    FOL goc:
        ∀i ∀j ∀v Given(i,j,v) ⇒ Val(i,j,v)

    CNF:
        Voi moi o (r,c) da cho gia tri v:
        Unit clause [Val(r,c,v)]
        → "o (r,c) PHAI la v"

    So clause: bang so o da cho trong puzzle

    Vi du: Given(0,1,2) → [Val(0,1,2)]
    """
    clauses = []
    for r in range(N):
        for c in range(N):
            if puzzle.grid[r][c] != 0:
                v = puzzle.grid[r][c]
                clauses.append([var_id(r, c, v, N)])
    return clauses


# ================================================================
# TONG HOP — tao toan bo ground KB
# ================================================================

def generate_ground_kb(puzzle):
    """
    Tao toan bo ground knowledge base dang CNF cho puzzle.

    Quy trinh:
      1. Voi moi axiom (A1–A9): ground hoa → tap cac clause propositional
      2. Ket hop tat ca clause thanh 1 formula CNF lon
         (CNF = conjunction cua tat ca clause)

    Parameters:
        puzzle (FutoshikiPuzzle): puzzle da doc tu file input

    Returns:
        all_clauses (list[list[int]]): tat ca clause CNF
            Moi clause la list cac literal (int)
            Literal duong = bien dung (Val co), am = bien sai (¬Val)
        num_vars (int): tong so bien propositional = N³
        clause_counts (dict): so clause sinh ra boi tung axiom
            (dung cho thong ke bao cao)
    """
    N = puzzle.N

    all_clauses = []
    clause_counts = {}  # thong ke tung axiom cho bao cao

    # ── A1: Moi o co it nhat 1 gia tri ──
    c = generate_at_least_one(N)
    clause_counts['A1 (at least one)  '] = len(c)
    all_clauses.extend(c)

    # ── A2: Moi o co nhieu nhat 1 gia tri ──
    c = generate_at_most_one(N)
    clause_counts['A2 (at most one)   '] = len(c)
    all_clauses.extend(c)

    # ── A3: Hang duy nhat ──
    c = generate_row_uniqueness(N)
    clause_counts['A3 (row unique)    '] = len(c)
    all_clauses.extend(c)

    # ── A6: Cot duy nhat ──
    c = generate_col_uniqueness(N)
    clause_counts['A6 (col unique)    '] = len(c)
    all_clauses.extend(c)

    # ── A4: Rang buoc ngang < ──
    c = generate_horizontal_less(N, puzzle)
    clause_counts['A4 (horiz <)       '] = len(c)
    all_clauses.extend(c)

    # ── A7: Rang buoc ngang > ──
    c = generate_horizontal_greater(N, puzzle)
    clause_counts['A7 (horiz >)       '] = len(c)
    all_clauses.extend(c)

    # ── A8: Rang buoc doc < ──
    c = generate_vertical_less(N, puzzle)
    clause_counts['A8 (vert <)        '] = len(c)
    all_clauses.extend(c)

    # ── A9: Rang buoc doc > ──
    c = generate_vertical_greater(N, puzzle)
    clause_counts['A9 (vert >)        '] = len(c)
    all_clauses.extend(c)

    # ── A5: Given clue bat buoc ──
    c = generate_given_clues(N, puzzle)
    clause_counts['A5 (given clues)   '] = len(c)
    all_clauses.extend(c)

    num_vars = N * N * N

    return all_clauses, num_vars, clause_counts


# ================================================================
# STATISTICS & OUTPUT — dung cho bao cao
# ================================================================

def print_cnf_stats(clauses, num_vars, clause_counts, N):
    """
    In thong ke CNF ra man hinh.

    Thong tin huu ich cho bao cao:
      - Tong so bien propositional (= N³)
      - Tong so clause CNF
      - So clause sinh ra boi tung axiom (de phan tich do phuc tap)
    """
    print(f"\n  {'=' * 46}")
    print(f"       CNF / GROUND KB STATISTICS")
    print(f"  {'=' * 46}")
    print(f"  Grid size           : {N} x {N}")
    print(f"  Total variables     : {num_vars} (= {N}³)")
    print(f"  Total clauses       : {len(clauses)}")
    print(f"  {'─' * 46}")
    print(f"  Phan bo theo axiom:")

    for axiom, count in clause_counts.items():
        print(f"    {axiom}: {count:>6} clauses")

    print(f"  {'─' * 46}")


def export_dimacs(clauses, num_vars, filepath):
    """
    Xuat CNF ra file DIMACS — format chuan quoc te cho SAT solver.

    DIMACS format:
      p cnf <num_vars> <num_clauses>
      <literal_1> <literal_2> ... 0     (moi dong la 1 clause, ket thuc bang 0)
      ...

    File nay co the dung voi bat ky SAT solver nao
    (MiniSat, Glucose, CryptoMiniSat, etc.)
    de verify ket qua doc lap.

    Parameters:
        clauses:  list[list[int]] — tat ca clause CNF
        num_vars: int — tong so bien
        filepath: str — duong dan file output
    """
    dir_path = os.path.dirname(filepath)
    if dir_path:
        os.makedirs(dir_path, exist_ok=True)

    with open(filepath, 'w') as f:
        f.write(f"c Futoshiki CNF - auto-generated\n")
        f.write(f"c Variables: Val(r,c,v) -> ID = r*N*N + c*N + (v-1) + 1\n")
        f.write(f"p cnf {num_vars} {len(clauses)}\n")
        for clause in clauses:
            f.write(" ".join(map(str, clause)) + " 0\n")

    print(f"  Da xuat DIMACS: {filepath}")


# ================================================================
# SAT SOLVER — dung pysat de giai
# ================================================================

def solve_with_pysat(clauses, num_vars, N):
    """
    Giai CNF bang pysat (Glucose4 solver).

    Glucose4 la 1 trong nhung SAT solver manh nhat hien nay,
    dua tren CDCL (Conflict-Driven Clause Learning).

    Parameters:
        clauses:  list[list[int]] — tat ca clause CNF
        num_vars: int — tong so bien
        N:        int — kich thuoc puzzle

    Returns:
        solution: dict {(r,c): value} neu SAT (co loi giai)
        None neu UNSAT (khong co loi giai)
    """
    try:
        from pysat.solvers import Glucose4
    except ImportError:
        print("\n  [Loi] Can cai dat python-sat:")
        print("        pip install python-sat")
        print("  Hoac chay: pip install -r requirements.txt\n")
        return None

    # Tao solver va them tat ca clause
    solver = Glucose4()

    for clause in clauses:
        solver.add_clause(clause)

    # Giai
    if solver.solve():
        model = solver.get_model()

        # Decode model → assignment dict
        # model la list cac literal: duong = true, am = false
        solution = {}
        for lit in model:
            if lit > 0 and lit <= num_vars:
                r, c, v = decode_var(lit, N)
                if 0 <= r < N and 0 <= c < N and 1 <= v <= N:
                    solution[(r, c)] = v

        solver.delete()
        return solution

    # UNSAT — khong co loi giai
    solver.delete()
    return None


# ================================================================
# PUBLIC INTERFACE — goi tu main.py
# ================================================================

def solve_cnf_generator(puzzle):
    """
    Entry point cho CNF solver — goi tu main.py.

    Quy trinh:
      1. Generate ground KB tu FOL axioms → CNF clauses
      2. In thong ke CNF (so bien, so clause, phan bo theo axiom)
      3. Xuat file DIMACS (de verify voi solver khac)
      4. Giai bang pysat Glucose4
      5. Tra ve (solution, stats)

    Parameters:
        puzzle (FutoshikiPuzzle): puzzle da doc tu file input

    Returns:
        solution: dict {(r,c): value} hoac None
        stats:    dict chua thong ke de in ra man hinh
    """
    N = puzzle.N

    # ── Buoc 1: Generate ground KB ──
    start_gen = time.time()
    clauses, num_vars, clause_counts = generate_ground_kb(puzzle)
    gen_time = time.time() - start_gen

    # ── Buoc 2: In thong ke ──
    print_cnf_stats(clauses, num_vars, clause_counts, N)
    print(f"  Thoi gian sinh KB  : {gen_time:.4f} giay")

    # ── Buoc 3: Xuat file DIMACS ──
    dimacs_path = os.path.join("Outputs", "futoshiki_cnf.dimacs")
    export_dimacs(clauses, num_vars, dimacs_path)

    # ── Buoc 4: Giai bang SAT solver ──
    print(f"\n  Dang giai bang SAT solver (Glucose4)...")
    start_solve = time.time()
    solution = solve_with_pysat(clauses, num_vars, N)
    solve_time = time.time() - start_solve

    # ── Buoc 5: Tao stats dict ──
    stats = {
        'nodes'       : len(clauses),       # so clause = "nodes" cho thong ke
        'time'        : gen_time + solve_time,
        'cnf_vars'    : num_vars,
        'cnf_clauses' : len(clauses),
        'gen_time'    : gen_time,
        'solve_time'  : solve_time,
    }

    return solution, stats
