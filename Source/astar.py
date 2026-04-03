#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
astar.py — A* Search Solver cho Futoshiki
Ho tro 3 heuristic:
  h1 : Trivial       — dem so o chua gan
  h2 : Domain Wipeout — phat hien dead-end som
  h3 : AC-3          — lan truyen rang buoc day du
"""

import heapq
import time
from collections import deque
from futoshiki import build_initial_assignment, compute_domain, compatible, get_neighbors


# ================================================================
# HEURISTIC 1 — Trivial
# ================================================================

def h1_unassigned(puzzle, assignment):
    """
    h(s) = so o chua duoc gan gia tri.

    Admissible : luon dung vi can it nhat h buoc nua.
    Do manh    : yeu — khong phan biet duoc state tot/xau.
    Chi phi    : O(1)
    """
    return puzzle.N * puzzle.N - len(assignment)


# ================================================================
# HEURISTIC 2 — Domain Wipeout
# ================================================================

def h2_domain_wipeout(puzzle, assignment):
    """
    Voi moi o chua gan, tinh domain con lai.
    Neu bat ky o nao domain rong → state vo nghiem → tra ve inf.
    Nguoc lai → tra ve so o chua gan (giong H1 nhung co pruning).

    Admissible : van tra ve so o chua gan <= h*,
                 chi them inf khi chac chan sai.
    Do manh    : trung binh — cat duoc dead-end ngay.
    Chi phi    : O(N^2) moi lan goi.
    """
    N = puzzle.N
    h = 0
    for r in range(N):
        for c in range(N):
            if (r, c) not in assignment:
                domain = compute_domain(puzzle, assignment, r, c)
                if len(domain) == 0:
                    return float('inf')  # Dead-end → prune
                h += 1
    return h


# ================================================================
# HEURISTIC 3 — AC-3
# ================================================================

def h3_ac3(puzzle, assignment):
    """
    Chay AC-3 (Arc Consistency 3) tren cac o chua gan.
    AC-3 lan truyen nhieu vong cho den khi khong doi,
    phat hien mau thuan sau hon H2.

    Admissible : AC-3 chi loai gia tri chac chan sai → khong overestimate.
    Do manh    : manh nhat — phat hien conflict chain.
    Chi phi    : O(N^3) moi lan goi.

    Return: tong kich thuoc domain con lai (cang nho → cang gan goal)
            hoac inf neu phat hien wipeout.
    """
    N = puzzle.N

    # Buoc 1: Khoi tao domains
    domains = {}
    for r in range(N):
        for c in range(N):
            if (r, c) not in assignment:
                dom = compute_domain(puzzle, assignment, r, c)
                if len(dom) == 0:
                    return float('inf')
                domains[(r, c)] = dom

    if not domains:
        return 0

    # Buoc 2: Tao queue cac arc
    queue = deque()
    for cell in domains:
        for neighbor in get_neighbors(puzzle, cell, assignment):
            if neighbor in domains:
                queue.append((cell, neighbor))

    # Buoc 3: Vong lap AC-3
    while queue:
        xi, xj = queue.popleft()

        if xi not in domains or xj not in domains:
            continue

        if _revise(puzzle, domains, xi, xj):
            if len(domains[xi]) == 0:
                return float('inf')  # Wipeout

            for xk in get_neighbors(puzzle, xi, assignment):
                if xk != xj and xk in domains:
                    queue.append((xk, xi))

    # Buoc 4: Tinh heuristic value
    return sum(len(d) for d in domains.values())


def _revise(puzzle, domains, xi, xj):
    """
    Loai cac gia tri trong domains[xi] khong co
    gia tri tuong thich nao trong domains[xj].
    Tra ve True neu domains[xi] bi thu hep.
    """
    ri, ci = xi
    rj, cj = xj
    revised = False
    to_remove = set()

    for vx in domains[xi]:
        has_support = any(
            compatible(puzzle, ri, ci, vx, rj, cj, vy)
            for vy in domains[xj]
        )
        if not has_support:
            to_remove.add(vx)
            revised = True

    domains[xi] -= to_remove
    return revised


# ================================================================
# MRV — Chon o tot nhat de expand
# ================================================================

def _pick_cell_mrv(domains_cache):
    """
    MRV: chon o chua gan co domain nho nhat.
    Giup A* uu tien giai quyet cac o kho truoc.
    """
    best_cell = None
    best_size = float('inf')

    for cell, domain in domains_cache.items():
        if len(domain) < best_size:
            best_cell = cell
            best_size = len(domain)
        if best_size == 1:
            break

    return best_cell, domains_cache.get(best_cell, set())


# ================================================================
# A* SOLVER CHINH
# ================================================================

def astar_solve(puzzle, heuristic='h2'):
    """
    Giai Futoshiki bang A* Search.

    Tham so:
        puzzle    : FutoshikiPuzzle object
        heuristic : 'h1' | 'h2' | 'h3'

    Tra ve:
        (assignment, stats) neu co loi giai
        (None, stats)       neu vo nghiem
    """
    heuristic_fn = {
        'h1': h1_unassigned,
        'h2': h2_domain_wipeout,
        'h3': h3_ac3,
    }.get(heuristic)

    if heuristic_fn is None:
        raise ValueError(f"Heuristic '{heuristic}' khong hop le. Chon: h1, h2, h3")

    N = puzzle.N
    initial = build_initial_assignment(puzzle)

    # Kiem tra ban dau
    h0 = heuristic_fn(puzzle, initial)
    if h0 == float('inf'):
        return None, {'nodes': 0, 'heuristic': heuristic}

    # Priority queue: (f, g, counter, assignment)
    counter = 0
    g0 = len(initial)
    heap = [(g0 + h0, g0, counter, initial)]

    visited = set()
    nodes_expanded = 0
    start_time = time.time()

    while heap:
        f, g, _, assignment = heapq.heappop(heap)

        state_key = tuple(sorted(assignment.items()))
        if state_key in visited:
            continue
        visited.add(state_key)
        nodes_expanded += 1

        # ── Goal check ──
        if len(assignment) == N * N:
            elapsed = time.time() - start_time
            stats = {
                'nodes'    : nodes_expanded,
                'time'     : elapsed,
                'heuristic': heuristic,
            }
            return assignment, stats

        # ── Tinh domain cho tat ca o chua gan ──
        domains_cache = {}
        dead_end = False
        for r in range(N):
            for c in range(N):
                if (r, c) not in assignment:
                    dom = compute_domain(puzzle, assignment, r, c)
                    if len(dom) == 0:
                        dead_end = True
                        break
                    domains_cache[(r, c)] = dom
            if dead_end:
                break

        if dead_end:
            continue

        # ── Chon o tot nhat (MRV) ──
        cell, domain = _pick_cell_mrv(domains_cache)
        if cell is None:
            continue

        r, c = cell

        # ── Expand: thu tung gia tri ──
        for v in sorted(domain):
            new_assignment = dict(assignment)
            new_assignment[(r, c)] = v

            new_state_key = tuple(sorted(new_assignment.items()))
            if new_state_key in visited:
                continue

            new_h = heuristic_fn(puzzle, new_assignment)
            if new_h == float('inf'):
                continue  # Prune

            new_g = len(new_assignment)
            counter += 1
            heapq.heappush(heap, (new_g + new_h, new_g, counter, new_assignment))

    # Khong tim duoc loi giai
    elapsed = time.time() - start_time
    stats = {
        'nodes'    : nodes_expanded,
        'time'     : elapsed,
        'heuristic': heuristic,
    }
    return None, stats


# ================================================================
# PUBLIC INTERFACE — goi tu main.py
# ================================================================

def solve_astar(puzzle, heuristic='h2'):
    """
    Wrapper tuong thich voi main.py.
    Tra ve (solution, stats) giong cac solver khac.
    """
    return astar_solve(puzzle, heuristic=heuristic)