# astar.py
# A* Search solver cho Futoshiki
# Hỗ trợ 3 heuristic: h1 (trivial), h2 (domain wipeout), h3 (AC-3)

import heapq
from collections import deque
from futoshiki import build_initial_assignment, compute_domain, compatible, get_neighbors


# ================================================================
# HEURISTIC 1 — Trivial: đếm số ô chưa gán
# ================================================================

def h1_unassigned(puzzle, assignment):
    """
    h(s) = số ô chưa được gán giá trị.

    Admissible: luôn đúng vì cần ít nhất h bước nữa.
    Độ mạnh  : yếu — không phân biệt được state tốt/xấu.
    Chi phí  : O(1)
    """
    return puzzle.N * puzzle.N - len(assignment)


# ================================================================
# HEURISTIC 2 — Domain Wipeout: phát hiện dead-end sớm
# ================================================================

def h2_domain_wipeout(puzzle, assignment):
    """
    Với mỗi ô chưa gán, tính domain còn lại.
    Nếu bất kỳ ô nào domain rỗng → state vô nghiệm → trả về inf.
    Ngược lại → trả về số ô chưa gán (giống H1 nhưng có pruning).

    Admissible: vẫn trả về số ô chưa gán ≤ h*, chỉ thêm inf khi chắc sai.
    Độ mạnh  : trung bình — cắt được dead-end ngay.
    Chi phí  : O(N²) mỗi lần gọi.
    """
    N = puzzle.N
    h = 0
    for r in range(N):
        for c in range(N):
            if (r, c) not in assignment:
                domain = compute_domain(puzzle, assignment, r, c)
                if len(domain) == 0:
                    return float('inf')  # Dead-end → prune ngay
                h += 1
    return h


# ================================================================
# HEURISTIC 3 — AC-3: lan truyền ràng buộc đầy đủ
# ================================================================

def h3_ac3(puzzle, assignment):
    """
    Chạy AC-3 (Arc Consistency 3) trên các ô chưa gán.
    AC-3 lan truyền nhiều vòng cho đến khi không đổi,
    phát hiện mâu thuẫn sâu hơn H2.

    Admissible: AC-3 chỉ loại giá trị chắc chắn sai → không overestimate.
    Độ mạnh  : mạnh nhất — phát hiện conflict chain.
    Chi phí  : O(N³) mỗi lần gọi — tốn hơn H1, H2.

    Return: tổng kích thước domain còn lại (càng nhỏ → càng gần goal)
            hoặc inf nếu phát hiện wipeout.
    """
    N = puzzle.N

    # --- Bước 1: Khởi tạo domains ---
    domains = {}
    for r in range(N):
        for c in range(N):
            if (r, c) not in assignment:
                dom = compute_domain(puzzle, assignment, r, c)
                if len(dom) == 0:
                    return float('inf')  # Wipeout ngay từ đầu
                domains[(r, c)] = dom

    # Nếu đã gán hết thì h = 0
    if not domains:
        return 0

    # --- Bước 2: Tạo queue các arc cần kiểm tra ---
    queue = deque()
    for cell in domains:
        for neighbor in get_neighbors(puzzle, cell, assignment):
            if neighbor in domains:
                queue.append((cell, neighbor))

    # --- Bước 3: Vòng lặp AC-3 ---
    while queue:
        xi, xj = queue.popleft()

        # xi hoặc xj có thể đã bị xóa khỏi domains (đã gán)
        if xi not in domains or xj not in domains:
            continue

        if _revise(puzzle, domains, xi, xj):
            if len(domains[xi]) == 0:
                return float('inf')  # Wipeout → vô nghiệm

            # Thêm tất cả neighbor của xi (trừ xj) vào queue để kiểm tra lại
            for xk in get_neighbors(puzzle, xi, assignment):
                if xk != xj and xk in domains:
                    queue.append((xk, xi))

    # --- Bước 4: Tính heuristic value ---
    # Tổng số giá trị còn lại trong tất cả domains
    # (domain càng bị thu hẹp → state càng bị ràng buộc → h phản ánh đúng hơn)
    return sum(len(d) for d in domains.values())


def _revise(puzzle, domains, xi, xj):
    """
    Loại các giá trị trong domains[xi] không có
    giá trị tương thích nào trong domains[xj].

    Trả về True nếu domains[xi] bị thu hẹp.
    """
    ri, ci = xi
    rj, cj = xj
    revised = False
    to_remove = set()

    for vx in domains[xi]:
        # Tìm ít nhất 1 vy trong domains[xj] tương thích với vx
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
# MRV — Chọn ô tốt nhất để expand tiếp theo
# ================================================================

def _pick_cell_mrv(puzzle, assignment, domains_cache):
    """
    Minimum Remaining Values: chọn ô chưa gán có domain nhỏ nhất.
    Giúp A* ưu tiên giải quyết các ô khó trước → cắt nhánh sớm hơn.

    domains_cache: dict {cell: domain} đã tính sẵn để tránh tính lại.
    """
    best_cell = None
    best_size = float('inf')

    for cell, domain in domains_cache.items():
        if len(domain) < best_size:
            best_cell = cell
            best_size = len(domain)
        if best_size == 1:
            break  # Không thể nhỏ hơn nữa

    return best_cell, domains_cache.get(best_cell, set())


# ================================================================
# A* SOLVER CHÍNH
# ================================================================

def astar_solve(puzzle, heuristic='h2'):
    """
    Giải Futoshiki bằng A* Search.

    Tham số:
        puzzle    : FutoshikiPuzzle object
        heuristic : 'h1' | 'h2' | 'h3'

    Trả về:
        assignment dict {(r,c): value} nếu có lời giải
        None nếu vô nghiệm

    Thống kê in ra:
        - Số nodes đã expand
        - Thời gian chạy
    """
    import time

    heuristic_fn = {
        'h1': h1_unassigned,
        'h2': h2_domain_wipeout,
        'h3': h3_ac3,
    }.get(heuristic)

    if heuristic_fn is None:
        raise ValueError(f"Heuristic '{heuristic}' không hợp lệ. Chọn: h1, h2, h3")

    N = puzzle.N
    initial = build_initial_assignment(puzzle)

    # Kiểm tra h ban đầu
    h0 = heuristic_fn(puzzle, initial)
    if h0 == float('inf'):
        return None  # Puzzle vô nghiệm ngay từ đầu

    # Priority queue: (f, g, counter, assignment)
    # counter để tránh so sánh dict khi f bằng nhau
    counter = 0
    g0 = len(initial)
    heap = [(g0 + h0, g0, counter, initial)]

    # Tập đã visited để tránh xử lý lại state cũ
    visited = set()

    # Thống kê
    nodes_expanded = 0
    start_time = time.time()

    while heap:
        f, g, _, assignment = heapq.heappop(heap)

        # Chuyển assignment thành hashable key
        state_key = tuple(sorted(assignment.items()))
        if state_key in visited:
            continue
        visited.add(state_key)
        nodes_expanded += 1

        # ── Goal check ──
        if len(assignment) == N * N:
            elapsed = time.time() - start_time
            print(f"[A*-{heuristic}] Solved!")
            print(f"  Nodes expanded : {nodes_expanded}")
            print(f"  Time           : {elapsed:.4f}s")
            return assignment

        # ── Tính domain cho tất cả ô chưa gán ──
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
            continue  # State này vô nghiệm, bỏ qua

        # ── Chọn ô tốt nhất để expand (MRV) ──
        cell, domain = _pick_cell_mrv(puzzle, assignment, domains_cache)
        if cell is None:
            continue

        r, c = cell

        # ── Expand: thử từng giá trị trong domain ──
        for v in sorted(domain):
            new_assignment = dict(assignment)
            new_assignment[(r, c)] = v

            new_state_key = tuple(sorted(new_assignment.items()))
            if new_state_key in visited:
                continue

            new_h = heuristic_fn(puzzle, new_assignment)
            if new_h == float('inf'):
                continue  # Prune — nhánh này chắc chắn vô nghiệm

            new_g = len(new_assignment)
            counter += 1
            heapq.heappush(heap, (new_g + new_h, new_g, counter, new_assignment))

    # Không tìm được lời giải
    elapsed = time.time() - start_time
    print(f"[A*-{heuristic}] No solution found.")
    print(f"  Nodes expanded : {nodes_expanded}")
    print(f"  Time           : {elapsed:.4f}s")
    return None