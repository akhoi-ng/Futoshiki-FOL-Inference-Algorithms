# main.py
import time, sys
from futoshiki import parse_input
# from backtracking import backtracking_solve
# from forward_chain import forward_chain_solve
# from backward_chain import backward_chain_solve
from astar import astar_solve
from display import print_solution, save_solution

ALGORITHMS = {
    # "bt"   : lambda puzzle, **kw: backtracking_solve(puzzle),
    # "fc"   : lambda puzzle, **kw: forward_chain_solve(puzzle),
    # "bc"   : lambda puzzle, **kw: backward_chain_solve(puzzle),
    "astar": lambda puzzle, **kw: astar_solve(puzzle, heuristic=kw.get('heuristic', 'h2')),
}

def run(input_file, algo_name, output_file=None, **kwargs):
    # 1. Load puzzle
    puzzle = parse_input(input_file)
    print(f"Puzzle {puzzle.N}x{puzzle.N} | Algorithm: {algo_name}")

    # 2. Lấy solver
    solver = ALGORITHMS.get(algo_name)
    if solver is None:
        print(f"Không tìm thấy thuật toán '{algo_name}'")
        print(f"Các thuật toán hợp lệ: {list(ALGORITHMS.keys())}")
        return

    # 3. Chạy
    try:
        start    = time.time()
        solution = solver(puzzle, **kwargs)
        elapsed  = time.time() - start
    except NotImplementedError as e:
        print(f"[{algo_name}] {e}")
        return

    # 4. In kết quả
    if solution:
        print(f"\n=== LỜI GIẢI ===")
        result = print_solution(puzzle, solution)
        print(f"\n[{algo_name}] Solved in {elapsed:.4f}s")
        if output_file:
            save_solution(puzzle, solution, output_file)
    else:
        print(f"[{algo_name}] Không tìm được lời giải. ({elapsed:.4f}s)")


if __name__ == "__main__":
    """
    Cách dùng:
      python main.py <input>  <algo>   [output]   [heuristic]
      python main.py input-01.txt astar            → dùng h2 mặc định
      python main.py input-01.txt astar out.txt h1 → dùng h1, lưu file
      python main.py input-01.txt astar out.txt h3 → dùng h3
    """
    if len(sys.argv) < 3:
        print("Cách dùng: python main.py <input_file> <algo> [output_file] [heuristic]")
        print("Algo: bt | fc | bc | astar")
        print("Heuristic (chỉ dùng với astar): h1 | h2 | h3")
        sys.exit(1)

    input_f    = sys.argv[1]
    algo       = sys.argv[2]
    output_f   = sys.argv[3] if len(sys.argv) > 3 else None
    heuristic  = sys.argv[4] if len(sys.argv) > 4 else 'h2'

    run(input_f, algo, output_f, heuristic=heuristic)
