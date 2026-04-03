def print_header(algorithm_name, input_file, grid_size):
    """In header cho chuong trinh."""
    print("\n" + "="*60)
    print(f"     FUTOSHIKI SOLVER - {algorithm_name.upper()}")
    print("="*60)
    print(f"Input: {input_file}")
    print(f"Kich thuoc: {grid_size}x{grid_size}")
    print("="*60)


def format_grid(puzzle, assignment):
    """Format grid thanh ASCII art voi cac rang buoc."""
    N = puzzle.N
    lines = []
    
    for r in range(N):
        # Main row
        row_parts = []
        for c in range(N):
            if (r, c) in assignment:
                val = str(assignment[(r, c)])
            else:
                val = "_"
            row_parts.append(val)
            
            # Horizontal constraint
            if c < N - 1:
                if puzzle.h_con[r][c] == 1:
                    row_parts.append("<")
                elif puzzle.h_con[r][c] == -1:
                    row_parts.append(">")
                else:
                    row_parts.append(" ")
        
        lines.append(" ".join(row_parts))
        
        # Vertical constraint row
        if r < N - 1:
            v_row_parts = []
            for c in range(N):
                if puzzle.v_con[r][c] == 1:
                    v_row_parts.append("^")
                elif puzzle.v_con[r][c] == -1:
                    v_row_parts.append("v")
                else:
                    v_row_parts.append(" ")
                
                if c < N - 1:
                    v_row_parts.append(" ")
            
            lines.append(" ".join(v_row_parts))
    
    return "\n".join(lines)


def format_statistics(stats):
    """Format statistics dictionary thanh string."""
    lines = ["\nThong ke:"]
    lines.append("-" * 40)
    
    if 'time' in stats:
        lines.append(f"  Thoi gian: {stats['time']:.3f} giay")
    
    if 'nodes' in stats:
        lines.append(f"  Nodes explored: {stats['nodes']}")
    
    if 'backtracks' in stats:
        lines.append(f"  Backtracks: {stats['backtracks']}")
    
    if 'inferences' in stats:
        lines.append(f"  Inferences made: {stats['inferences']}")
    
    if 'iterations' in stats:
        lines.append(f"  Iterations: {stats['iterations']}")
    
    if 'depth' in stats:
        lines.append(f"  Solution depth: {stats['depth']}")
    
    lines.append("-" * 40)
    
    return "\n".join(lines)


def save_solution(assignment, N, filepath):
    """Luu solution vao file."""
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f"{N}\n")
        
        for r in range(N):
            row_values = []
            for c in range(N):
                if (r, c) in assignment:
                    row_values.append(str(assignment[(r, c)]))
                else:
                    row_values.append("0")
            
            f.write(",".join(row_values) + "\n")


def print_debug_domains(domains):
    """In ra domains cua cac cells (for debugging)."""
    print("\nDomains hien tai:")
    for (r, c), vals in sorted(domains.items()):
        vals_str = "{" + ",".join(map(str, sorted(vals))) + "}"
        print(f"  Cell ({r},{c}): {vals_str}")
