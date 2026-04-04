
# ================================================================
# HEADER
# ================================================================

def print_header(algorithm_name, input_file, grid_size):
    """In header cho chương trình."""
    print("\n" + "=" * 60)
    print(f"     FUTOSHIKI SOLVER - {algorithm_name.upper()}")
    print("=" * 60)
    print(f"  Input : {input_file}")
    print(f"  Size  : {grid_size}x{grid_size}")
    print("=" * 60)


# ================================================================
# FORMAT GRID — đúng theo yêu cầu đề bài
# ================================================================

def format_grid(puzzle, assignment):
    """
    Format lời giải thành chuỗi ASCII với đầy đủ ký hiệu:
      <, >  : horizontal inequality
      ^     : top < bottom  (vertical)
      v     : top > bottom  (vertical)

    Đây là format đề bài yêu cầu trong output.
    """
    N = puzzle.N
    lines = []

    for r in range(N):
        # ── Hàng số ──
        row_parts = []
        for c in range(N):
            val = str(assignment[(r, c)]) if (r, c) in assignment else "_"
            row_parts.append(val)

            if c < N - 1:
                con = puzzle.h_con[r][c]
                if con == 1:
                    row_parts.append("<")
                elif con == -1:
                    row_parts.append(">")
                else:
                    row_parts.append(" ")

        lines.append(" ".join(row_parts))

        # ── Hàng ký hiệu vertical (trừ hàng cuối) ──
        if r < N - 1:
            v_parts = []
            for c in range(N):
                con = puzzle.v_con[r][c]
                if con == 1:
                    v_parts.append("^")
                elif con == -1:
                    v_parts.append("v")
                else:
                    v_parts.append(" ")

                if c < N - 1:
                    v_parts.append(" ")

            lines.append(" ".join(v_parts))

    return "\n".join(lines)


def print_solution(puzzle, assignment):
    """In lời giải ra màn hình và trả về string."""
    result = format_grid(puzzle, assignment)
    print(result)
    return result


# ================================================================
# STATISTICS
# ================================================================

def format_statistics(stats):
    """
    Format dict thống kê thành chuỗi đẹp.
    Dùng cho báo cáo — hỗ trợ mọi key có thể có.
    """
    lines = ["\n  Thong ke:"]
    lines.append("  " + "-" * 38)

    key_labels = {
        'time'        : "Thoi gian",
        'nodes'       : "Nodes explored",
        'backtracks'  : "Backtracks",
        'inferences'  : "Inferences made",
        'iterations'  : "FC Iterations",
        'depth'       : "Solution depth",
        'heuristic'   : "Heuristic",
        'cnf_vars'    : "CNF variables",
        'cnf_clauses' : "CNF clauses",
        'gen_time'    : "KB generation time",
        'solve_time'  : "SAT solve time",
    }

    for key, label in key_labels.items():
        if key in stats:
            val = stats[key]
            if key in ('time', 'gen_time', 'solve_time'):
                lines.append(f"  {label:<20}: {val:.4f} giay")
            else:
                lines.append(f"  {label:<20}: {val}")

    lines.append("  " + "-" * 38)
    return "\n".join(lines)


# ================================================================
# SAVE — lưu đúng format đề bài (có ký hiệu <, >, ^, v)
# ================================================================

def save_solution(puzzle, assignment, filepath):
    """
    Lưu lời giải ra file với đầy đủ ký hiệu,
    đúng format đề bài yêu cầu.
    """
    import os
    os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else '.', exist_ok=True)

    result = format_grid(puzzle, assignment)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(result + "\n")

    print(f"  Da luu ket qua vao: {filepath}")


# ================================================================
# DEBUG
# ================================================================

def print_debug_domains(domains):
    """In domains của các ô — dùng khi debug."""
    print("\n  [DEBUG] Domains hien tai:")
    for (r, c), vals in sorted(domains.items()):
        vals_str = "{" + ", ".join(map(str, sorted(vals))) + "}"
        print(f"    O ({r},{c}): {vals_str}")