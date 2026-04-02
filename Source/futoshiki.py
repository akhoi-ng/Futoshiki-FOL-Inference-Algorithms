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