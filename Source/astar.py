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
# LỚP 1: INFERENCE (SUY DIỄN & LỌC DOMAIN)
# ================================================================

def get_filtered_domains(puzzle, assignment, apply_ac3=False):
    """
    Tính toán domain cho tất cả ô chưa gán.
    Nếu apply_ac3 = True, chạy thêm thuật toán AC-3 để lọc sâu.
    Trả về: domains_cache (dict) hoặc None (nếu phát hiện vô nghiệm).
    """
    N = puzzle.N
    domains_cache = {}
    
    # 1. Forward Checking cơ bản (Tính domain ban đầu)
    for r in range(N):
        for c in range(N):
            if (r, c) not in assignment:
                dom = compute_domain(puzzle, assignment, r, c)
                if len(dom) == 0:
                    return None  # Wipeout
                domains_cache[(r, c)] = dom

    # 2. MAC (Maintaining Arc Consistency) - Lọc sâu
    if apply_ac3:
        queue = deque()
        for cell in domains_cache:
            for neighbor in get_neighbors(puzzle, cell, assignment):
                if neighbor in domains_cache:
                    queue.append((cell, neighbor))

        while queue:
            xi, xj = queue.popleft()
            if xi not in domains_cache or xj not in domains_cache:
                continue
                
            if _revise(puzzle, domains_cache, xi, xj):
                if len(domains_cache[xi]) == 0:
                    return None  # Wipeout sau khi lan truyền
                for xk in get_neighbors(puzzle, xi, assignment):
                    if xk != xj and xk in domains_cache:
                        queue.append((xk, xi))
                        
    return domains_cache

# ================================================================
# LỚP 2: HEURISTICS (HÀM ĐÁNH GIÁ)
# ================================================================

def h1_unassigned(puzzle, assignment):
    return puzzle.N * puzzle.N - len(assignment)


def h2_inequality_chains(puzzle, assignment):
    """
    Gợi ý 2: Đếm số phép gán tối thiểu để hoàn thành các chuỗi bất đẳng thức.
    """
    # 1. Kế thừa sức mạnh Cắt tỉa (Pruning) của Domain Wipeout
    # (Bắt buộc phải có để A* không bị bùng nổ không gian mẫu)
    domains_cache = get_filtered_domains(puzzle, assignment, apply_ac3=False)
    if domains_cache is None:
        return float('inf')

    N = puzzle.N
    visited_cells = set()
    h_chains_cost = 0

    # Hàm phụ trợ: Dùng BFS để tìm toàn bộ các ô trong cùng 1 chuỗi bất đẳng thức
    def get_chain_component(start_r, start_c):
        component = []
        queue = deque([(start_r, start_c)])
        visited_cells.add((start_r, start_c))

        while queue:
            r, c = queue.popleft()
            component.append((r, c))

            neighbors_with_constraints = []
            # Kiểm tra Ngang Trái
            if c > 0 and puzzle.h_con[r][c-1] != 0:
                neighbors_with_constraints.append((r, c-1))
            # Kiểm tra Ngang Phải
            if c < N - 1 and puzzle.h_con[r][c] != 0:
                neighbors_with_constraints.append((r, c+1))
            # Kiểm tra Dọc Trên
            if r > 0 and puzzle.v_con[r-1][c] != 0:
                neighbors_with_constraints.append((r-1, c))
            # Kiểm tra Dọc Dưới
            if r < N - 1 and puzzle.v_con[r][c] != 0:
                neighbors_with_constraints.append((r+1, c))

            for nr, nc in neighbors_with_constraints:
                if (nr, nc) not in visited_cells:
                    visited_cells.add((nr, nc))
                    queue.append((nr, nc))
                    
        return component

    # 2. Quét toàn bộ bàn cờ để tìm các chuỗi
    for r in range(N):
        for c in range(N):
            if (r, c) not in visited_cells:
                # Kiểm tra xem ô này có dính dáng tới dấu <, > nào không
                has_constraint = False
                if c > 0 and puzzle.h_con[r][c-1] != 0: has_constraint = True
                elif c < N - 1 and puzzle.h_con[r][c] != 0: has_constraint = True
                elif r > 0 and puzzle.v_con[r-1][c] != 0: has_constraint = True
                elif r < N - 1 and puzzle.v_con[r][c] != 0: has_constraint = True

                if has_constraint:
                    # Lấy ra toàn bộ chuỗi chứa ô này
                    chain = get_chain_component(r, c)
                    
                    # Đếm số ô CÒN TRỐNG (chưa được gán) trong chuỗi này
                    unassigned_in_chain = sum(1 for cell in chain if cell not in assignment)
                    
                    # Nếu chuỗi có ô trống (unfulfilled), ta phải tốn số phép gán bằng đúng số ô trống đó
                    if unassigned_in_chain > 0:
                        h_chains_cost += unassigned_in_chain
    return h_chains_cost

def h3_ac3(puzzle, assignment):
    domains_cache = get_filtered_domains(puzzle, assignment, apply_ac3=True)
    if domains_cache is None:
        return float('inf')
    # Điểm h = tổng kích thước các domain còn lại
    return sum(len(d) for d in domains_cache.values())



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
# LỚP 3: A* SOLVER CHÍNH
# ================================================================

def astar_solve(puzzle, heuristic='h2', step_callback=None):
    heuristic_fn = {
        'h1': h1_unassigned,
        'h2': h2_inequality_chains,
        'h3': h3_ac3,
    }.get(heuristic)

    if heuristic_fn is None:
        raise ValueError("Heuristic không hợp lệ!")

    N = puzzle.N
    initial = build_initial_assignment(puzzle)

    h0 = heuristic_fn(puzzle, initial)
    if h0 == float('inf'):
        return None, {'nodes': 0, 'heuristic': heuristic}

    counter = 0
    g0 = len(initial)
    heap = [(g0 + h0, -g0, counter, initial)]
    visited = set()
    step_count = 0
    nodes_expanded = 0
    start_time = time.time()

    while heap:
        f, neg_g, _, assignment = heapq.heappop(heap)
        g = -neg_g
        
        state_key = tuple(sorted(assignment.items()))
        if state_key in visited:
            continue
        visited.add(state_key)
        nodes_expanded += 1

        # Notify GUI
        if step_callback:
            step_count += 1
            step_callback({
                'type': 'expand',
                'message': f'[A*] Expand node #{nodes_expanded}, f={f}, g={g}, cells={len(assignment)}/{N*N}',
                'assignment': dict(assignment),
                'cell': None,
                'value': None,
                'step_number': step_count,
            })

        
        if len(assignment) == N * N:
            return assignment, {'nodes': nodes_expanded, 'time': time.time() - start_time, 'heuristic': heuristic}

        # ── 1. Tính Domains cho trạng thái HIỆN TẠI (Để MRV chọn ô) ──
        # Nếu đang dùng h3, ta cho MRV hưởng ké sức mạnh của AC-3 để chọn ô thông minh
        use_ac3 = (heuristic == 'h3')
        domains_cache = get_filtered_domains(puzzle, assignment, apply_ac3=use_ac3)
        
        if domains_cache is None:
            continue  # Dead-end

        # ── 2. Chọn ô tốt nhất (MRV) ──
        cell, domain = _pick_cell_mrv(domains_cache)
        if cell is None:
            continue

        # ── 3. Expand: Sinh nhánh con ──
        r, c = cell
        for v in sorted(domain):
            new_assignment = dict(assignment)
            new_assignment[(r, c)] = v

            # ── 4. THẨM ĐỊNH NHÁNH CON (Gọi Heuristic) ──
            new_h = heuristic_fn(puzzle, new_assignment)
            
            if new_h == float('inf'):
                continue  # Bị Heuristic đánh trượt -> Prune ngay lập tức

            new_g = len(new_assignment)
            counter += 1
            heapq.heappush(heap, (new_g + new_h, -new_g, counter, new_assignment))

    return None, {'nodes': nodes_expanded, 'time': time.time() - start_time, 'heuristic': heuristic}



# ================================================================
# PUBLIC INTERFACE — goi tu main.py
# ================================================================

def solve_astar(puzzle, heuristic='h2', step_callback=None):
    """
    Wrapper tuong thich voi main.py.
    Tra ve (solution, stats) giong cac solver khac.
    """
    return astar_solve(puzzle, heuristic=heuristic, step_callback=step_callback)