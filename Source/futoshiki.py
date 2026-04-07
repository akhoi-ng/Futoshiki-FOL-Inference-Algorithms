class FutoshikiPuzzle:
    """
    Đại diện cho một puzzle Futoshiki.
    Index dùng 0-based trong code (row 0..N-1, col 0..N-1)
    nhưng FOL notation dùng 1-based (để khớp với đề bài).
    """

    def __init__(self, N, grid, h_con, v_con):
        self.N = N
        # grid[r][c] = 0 (trống) hoặc 1..N (đã điền)
        self.grid = grid
        # h_con[r][c]: ràng buộc giữa (r,c) và (r,c+1)
        #   0 = không có,  1 = '<',  -1 = '>'
        self.h_con = h_con
        # v_con[r][c]: ràng buộc giữa (r,c) và (r+1,c)
        self.v_con = v_con

    def get_domain(self, assignment):
        """
        Trả về domain (tập giá trị có thể) cho mỗi ô trống,
        dựa trên assignment hiện tại.
        assignment: dict {(r,c): value}
        """
        domains = {}
        for r in range(self.N):
            for c in range(self.N):
                if (r, c) not in assignment:
                    domains[(r, c)] = set(range(1, self.N + 1))
        return domains

    def is_valid(self, assignment):
        """Kiểm tra assignment có vi phạm ràng buộc không."""
        N = self.N
        # Kiểm tra hàng
        for r in range(N):
            vals = [assignment[(r, c)] for c in range(N) if (r, c) in assignment]
            if len(vals) != len(set(vals)):
                return False
        # Kiểm tra cột
        for c in range(N):
            vals = [assignment[(r, c)] for r in range(N) if (r, c) in assignment]
            if len(vals) != len(set(vals)):
                return False
        # Kiểm tra H-constraints
        for r in range(N):
            for c in range(N - 1):
                if self.h_con[r][c] != 0:
                    if (r, c) in assignment and (r, c + 1) in assignment:
                        v1, v2 = assignment[(r, c)], assignment[(r, c + 1)]
                        if self.h_con[r][c] == 1 and not v1 < v2:
                            return False
                        if self.h_con[r][c] == -1 and not v1 > v2:
                            return False
        # Kiểm tra V-constraints
        for r in range(N - 1):
            for c in range(N):
                if self.v_con[r][c] != 0:
                    if (r, c) in assignment and (r + 1, c) in assignment:
                        v1, v2 = assignment[(r, c)], assignment[(r + 1, c)]
                        if self.v_con[r][c] == 1 and not v1 < v2:
                            return False
                        if self.v_con[r][c] == -1 and not v1 > v2:
                            return False
        return True


def parse_input(filepath):
    """Đọc file input, trả về FutoshikiPuzzle."""
    with open(filepath) as f:
        lines = [l.strip() for l in f if l.strip()]

    idx = 0
    N = int(lines[idx]); idx += 1

    grid = []
    for _ in range(N):
        grid.append(list(map(int, lines[idx].split(',')))); idx += 1

    h_con = []
    for _ in range(N):
        h_con.append(list(map(int, lines[idx].split(',')))); idx += 1

    v_con = []
    for _ in range(N - 1):
        v_con.append(list(map(int, lines[idx].split(',')))); idx += 1

    return FutoshikiPuzzle(N, grid, h_con, v_con)


def build_initial_assignment(puzzle):
    """
    Chuyển grid (các ô đã cho) thành assignment dict.
    Đây chính là tập FACTS ban đầu trong FOL.
    """
    assignment = {}
    for r in range(puzzle.N):
        for c in range(puzzle.N):
            if puzzle.grid[r][c] != 0:
                assignment[(r, c)] = puzzle.grid[r][c]
    return assignment


# ================================================================
# UTILITY FUNCTIONS — dùng chung cho FC, BC, A*
# ================================================================

def compute_domain(puzzle, assignment, r, c, domains=None):
    """
    Tính tập giá trị còn hợp lệ cho ô (r, c)
    dựa trên assignment hiện tại.
    Áp dụng: row/col uniqueness + inequality constraints.

    Nếu domains (dict {(r,c): set}) được cung cấp, sử dụng
    min/max của domain ô kề chưa gán để bound pruning chính xác hơn
    (arc-consistent bound estimation) thay vì chỉ loại cực trị.
    """
    N = puzzle.N

    # Loại giá trị đã dùng trong hàng và cột
    used_row = {assignment[(r, col)] for col in range(N) if (r, col) in assignment}
    used_col = {assignment[(row, c)] for row in range(N) if (row, c) in assignment}
    domain = set(range(1, N + 1)) - used_row - used_col

    # H-constraint: (r, c-1) < (r, c)  →  v > left
    if c > 0 and puzzle.h_con[r][c - 1] == 1:
        left = assignment.get((r, c - 1))
        if left is not None:
            domain = {v for v in domain if v > left}
        elif domains and (r, c - 1) in domains and domains[(r, c - 1)]:
            domain = {v for v in domain if v > min(domains[(r, c - 1)])}
        else:
            domain.discard(1)   # phải > ô trái → không thể là 1

    # H-constraint: (r, c-1) > (r, c)  →  v < left
    if c > 0 and puzzle.h_con[r][c - 1] == -1:
        left = assignment.get((r, c - 1))
        if left is not None:
            domain = {v for v in domain if v < left}
        elif domains and (r, c - 1) in domains and domains[(r, c - 1)]:
            domain = {v for v in domain if v < max(domains[(r, c - 1)])}
        else:
            domain.discard(N)   # phải < ô trái → không thể là N

    # H-constraint: (r, c) < (r, c+1)  →  v < right
    if c < N - 1 and puzzle.h_con[r][c] == 1:
        right = assignment.get((r, c + 1))
        if right is not None:
            domain = {v for v in domain if v < right}
        elif domains and (r, c + 1) in domains and domains[(r, c + 1)]:
            domain = {v for v in domain if v < max(domains[(r, c + 1)])}
        else:
            domain.discard(N)   # phải < ô phải → không thể là N

    # H-constraint: (r, c) > (r, c+1)  →  v > right
    if c < N - 1 and puzzle.h_con[r][c] == -1:
        right = assignment.get((r, c + 1))
        if right is not None:
            domain = {v for v in domain if v > right}
        elif domains and (r, c + 1) in domains and domains[(r, c + 1)]:
            domain = {v for v in domain if v > min(domains[(r, c + 1)])}
        else:
            domain.discard(1)   # phải > ô phải → không thể là 1

    # V-constraint: (r-1, c) < (r, c)  →  v > top
    if r > 0 and puzzle.v_con[r - 1][c] == 1:
        top = assignment.get((r - 1, c))
        if top is not None:
            domain = {v for v in domain if v > top}
        elif domains and (r - 1, c) in domains and domains[(r - 1, c)]:
            domain = {v for v in domain if v > min(domains[(r - 1, c)])}
        else:
            domain.discard(1)   # phải > ô trên → không thể là 1

    # V-constraint: (r-1, c) > (r, c)  →  v < top
    if r > 0 and puzzle.v_con[r - 1][c] == -1:
        top = assignment.get((r - 1, c))
        if top is not None:
            domain = {v for v in domain if v < top}
        elif domains and (r - 1, c) in domains and domains[(r - 1, c)]:
            domain = {v for v in domain if v < max(domains[(r - 1, c)])}
        else:
            domain.discard(N)   # phải < ô trên → không thể là N

    # V-constraint: (r, c) < (r+1, c)  →  v < bot
    if r < N - 1 and puzzle.v_con[r][c] == 1:
        bot = assignment.get((r + 1, c))
        if bot is not None:
            domain = {v for v in domain if v < bot}
        elif domains and (r + 1, c) in domains and domains[(r + 1, c)]:
            domain = {v for v in domain if v < max(domains[(r + 1, c)])}
        else:
            domain.discard(N)   # phải < ô dưới → không thể là N

    # V-constraint: (r, c) > (r+1, c)  →  v > bot
    if r < N - 1 and puzzle.v_con[r][c] == -1:
        bot = assignment.get((r + 1, c))
        if bot is not None:
            domain = {v for v in domain if v > bot}
        elif domains and (r + 1, c) in domains and domains[(r + 1, c)]:
            domain = {v for v in domain if v > min(domains[(r + 1, c)])}
        else:
            domain.discard(1)   # phải > ô dưới → không thể là 1

    return domain


def compatible(puzzle, ri, ci, vi, rj, cj, vj):
    """
    Kiểm tra gán (ri,ci)=vi và (rj,cj)=vj có mâu thuẫn không.
    Dùng trong AC-3 để kiểm tra từng cặp giá trị.
    """
    # Cùng hàng hoặc cùng cột → không được trùng giá trị
    if (ri == rj or ci == cj) and vi == vj:
        return False

    # H-constraint giữa 2 ô liền nhau cùng hàng
    if ri == rj and abs(ci - cj) == 1:
        c_left = min(ci, cj)
        con = puzzle.h_con[ri][c_left]
        v_left  = vi if ci == c_left else vj
        v_right = vj if ci == c_left else vi
        if con == 1  and not v_left < v_right:
            return False
        if con == -1 and not v_left > v_right:
            return False

    # V-constraint giữa 2 ô liền nhau cùng cột
    if ci == cj and abs(ri - rj) == 1:
        r_top = min(ri, rj)
        con = puzzle.v_con[r_top][ci]
        v_top = vi if ri == r_top else vj
        v_bot = vj if ri == r_top else vi
        if con == 1  and not v_top < v_bot:
            return False
        if con == -1 and not v_top > v_bot:
            return False

    return True


def get_neighbors(puzzle, cell, assignment):
    """
    Trả về tất cả ô chưa gán có ràng buộc với cell:
    cùng hàng, cùng cột, hoặc kề nhau có inequality.
    """
    r, c = cell
    N = puzzle.N
    neighbors = set()

    for col in range(N):
        if col != c and (r, col) not in assignment:
            neighbors.add((r, col))
    for row in range(N):
        if row != r and (row, c) not in assignment:
            neighbors.add((row, c))

    return neighbors