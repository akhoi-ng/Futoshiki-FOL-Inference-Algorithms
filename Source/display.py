def print_solution(puzzle, assignment):
    """In lời giải ra màn hình với ký hiệu <, >, ^, v"""
    N = puzzle.N
    lines = []

    for r in range(N):
        # In hàng số
        row_parts = []
        for c in range(N):
            row_parts.append(str(assignment[(r, c)]))
            if c < N - 1:
                con = puzzle.h_con[r][c]
                if con == 1:
                    row_parts.append('<')
                elif con == -1:
                    row_parts.append('>')
                else:
                    row_parts.append(' ')
        lines.append(' '.join(row_parts))

        # In hàng ký hiệu vertical (trừ hàng cuối)
        if r < N - 1:
            v_parts = []
            for c in range(N):
                con = puzzle.v_con[r][c]
                if con == 1:
                    v_parts.append('^')
                elif con == -1:
                    v_parts.append('v')
                else:
                    v_parts.append(' ')
            lines.append(' '.join(v_parts))

    result = '\n'.join(lines)
    print(result)
    return result


def save_solution(puzzle, assignment, output_path):
    """Lưu lời giải ra file txt"""
    result = print_solution(puzzle, assignment)
    with open(output_path, 'w') as f:
        f.write(result)
    print(f"\nĐã lưu vào: {output_path}")