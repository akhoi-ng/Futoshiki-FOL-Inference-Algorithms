#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
main.py — Futoshiki Solver Entry Point
CSC14003 - Co so Tri tue Nhan tao

Cach dung:
  python main.py <input_file> <algorithm> [output_file] [heuristic]

Algorithm:
  fc    : Forward Chaining
  bt    : Backtracking
  bc    : Backward Chaining
  astar : A* Search
  cnf   : CNF Generator      (chua implement)

Heuristic (chi dung voi astar):
  h1 : Trivial (dem o chua gan)
  h2 : Domain Wipeout         (mac dinh)
  h3 : AC-3

Vi du:
  python main.py Inputs/input-01.txt fc
  python main.py Inputs/input-01.txt bt    Outputs/output-01.txt
  python main.py Inputs/input-01.txt astar Outputs/output-01.txt h2
  python main.py Inputs/input-01.txt astar Outputs/output-01.txt h3
"""

import sys
import time
import argparse
from pathlib import Path

from futoshiki import parse_input, build_initial_assignment
from forward_chain import solve_forward_chaining
from backtracking import solve_backtracking
from backward_chain import solve_backward_chaining
from astar import solve_astar
from cnf_generator import solve_cnf_generator
from display import (
    print_header,
    format_grid,
    format_statistics,
    print_solution,
    save_solution,
)

# ================================================================
# ALGORITHM REGISTRY
# ================================================================

ALGO_NAMES = {
    'fc'   : 'Forward Chaining',
    'bt'   : 'Backtracking',
    'bc'   : 'Backward Chaining',
    'astar': 'A* Search',
    'cnf'  : 'CNF Generator',
}

NOT_IMPLEMENTED = {}


# ================================================================
# ARGUMENT PARSING
# ================================================================

def parse_arguments():
    parser = argparse.ArgumentParser(
        description='Giai Futoshiki bang cac thuat toan FOL inference',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Vi du:
  python main.py Inputs/input-01.txt fc
  python main.py Inputs/input-01.txt bt    Outputs/output-01.txt
  python main.py Inputs/input-01.txt astar Outputs/output-01.txt h2
  python main.py Inputs/input-01.txt astar Outputs/output-01.txt h3
        """
    )

    parser.add_argument(
        'input_file',
        help='Duong dan den file input (.txt)'
    )
    parser.add_argument(
        'algorithm',
        choices=list(ALGO_NAMES.keys()),
        help='Thuat toan: fc | bt | bc | astar | cnf'
    )
    parser.add_argument(
        'output_file',
        nargs='?',
        default=None,
        help='Duong dan file output (optional)'
    )
    parser.add_argument(
        'heuristic',
        nargs='?',
        default='h2',
        choices=['h1', 'h2', 'h3'],
        help='Heuristic cho A* (mac dinh: h2)'
    )

    return parser.parse_args()


# ================================================================
# SOLVER DISPATCHER
# ================================================================

def run_solver(puzzle, algorithm, heuristic='h2', step_callback=None):
    """
    Chay thuat toan tuong ung va tra ve (solution, stats).
    Tat ca solver deu tra ve (solution, stats) de thong nhat.
    """
    if algorithm == 'fc':
        return solve_forward_chaining(puzzle, step_callback=step_callback)

    elif algorithm == 'bt':
        return solve_backtracking(puzzle, step_callback=step_callback)

    elif algorithm == 'bc':
        from backward_chain import BackwardChainingSolver
        solver = BackwardChainingSolver(puzzle, step_callback=step_callback)
        solution, stats = solver.solve()

        # Demo Prolog-style query neu giai duoc
        if solution:
            print("\n  [BC] Prolog-style query — Val(i, j, ?) cho tung o:")
            print("  " + "-" * 44)
            N = solver.N
            for r in range(N):
                row_q = []
                for c in range(N):
                    vals = solver.query_cell_values(r + 1, c + 1, one_based=True)
                    v = vals[0] if vals else "?"
                    row_q.append(f"Val({r+1},{c+1},V)={v}")
                print("  " + "   ".join(row_q))
            print("  " + "-" * 44)

            print("\n  [BC] Demo query yes/no:")
            done = 0
            for r in range(N):
                for c in range(N):
                    vals = solver.query_cell_values(r + 1, c + 1, one_based=True)
                    if vals:
                        v_true  = vals[0]
                        v_false = (v_true % N) + 1
                        res_t = solver.query_cell_is(r+1, c+1, v_true,  one_based=True)
                        res_f = solver.query_cell_is(r+1, c+1, v_false, one_based=True)
                        print(f"    ?- Val({r+1},{c+1},{v_true}).  ->  {'Yes' if res_t else 'No'}"
                            f"   |   ?- Val({r+1},{c+1},{v_false}).  ->  {'Yes' if res_f else 'No'}")
                        done += 1
                    if done == 3:
                        break
                if done == 3:
                    break

        return solution, stats

    elif algorithm == 'astar':
        return solve_astar(puzzle, heuristic=heuristic, step_callback=step_callback)

    elif algorithm == 'cnf':
        return solve_cnf_generator(puzzle, step_callback=step_callback)

    elif algorithm in NOT_IMPLEMENTED:
        raise NotImplementedError(
            f"'{ALGO_NAMES[algorithm]}' chua duoc implement."
        )

    else:
        raise ValueError(f"Thuat toan khong hop le: '{algorithm}'")


# ================================================================
# MAIN
# ================================================================

def main():
    args = parse_arguments()

    # ── Kiem tra file ton tai ──
    input_path = Path(args.input_file)
    if not input_path.exists():
        print(f"\n[Loi] Khong tim thay file: '{args.input_file}'")
        print(f"      Duong dan: {input_path.absolute()}")
        return 1

    algo_name = ALGO_NAMES.get(args.algorithm, args.algorithm.upper())

    try:
        # ── Load puzzle ──
        puzzle = parse_input(str(input_path))
        initial_assignment = build_initial_assignment(puzzle)

        # ── Header ──
        print_header(algo_name, args.input_file, puzzle.N)

        # ── In trang thai ban dau ──
        print("\n  Trang thai ban dau:")
        print(format_grid(puzzle, initial_assignment))

        # ── A* heuristic info ──
        if args.algorithm == 'astar':
            heuristic_desc = {
                'h1': 'H1 - Trivial (dem o chua gan)',
                'h2': 'H2 - Counting Inequality Chains',
                'h3': 'H3 - AC-3',
            }
            print(f"\n  Heuristic: {heuristic_desc[args.heuristic]}")

        print("\n  Dang giai...")

        # ── Giai ──
        start_time = time.time()
        solution, stats = run_solver(puzzle, args.algorithm, args.heuristic)
        end_time = time.time()

        # Them thoi gian vao stats (do chinh xac hon tu main)
        if 'time' not in stats:
            stats['time'] = round(end_time - start_time, 4) # type: ignore

        # ── Ket qua ──
        if solution:
            print(f"\n  Tim thay loi giai!\n")
            print(format_grid(puzzle, solution))
            print(format_statistics(stats))

            # FC-specific: ghi ro FC co giai duoc hoan toan khong
            if args.algorithm == 'fc' and 'fc_solved' in stats:
                if stats['fc_solved']:
                    print("  [FC] Giai duoc hoan toan bang Forward Chaining.")
                else:
                    print("  [FC] FC dat fixpoint, Backtracking ho tro phan con lai.")

            # Luu output
            if args.output_file:
                output_path = Path(args.output_file)
                save_solution(puzzle, solution, str(output_path))

            print("\n" + "=" * 60)
            return 0

        else:
            print(f"\n  Khong tim thay loi giai!")
            print(format_statistics(stats))
            print("\n" + "=" * 60)
            return 1

    except NotImplementedError as e:
        print(f"\n  [Chua implement] {e}")
        print("  Hay chay: fc, bt, bc, hoac astar.\n")
        return 1

    except FileNotFoundError as e:
        print(f"\n  [Loi] Khong tim thay file: {e}")
        return 1

    except ValueError as e:
        print(f"\n  [Loi] Du lieu khong hop le: {e}")
        return 1

    except Exception as e:
        print(f"\n  [Loi khong mong doi] {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    # Neu khong co tham so command line -> chay GUI
    if len(sys.argv) <= 1:
        from gui import FutoshikiApp
        app = FutoshikiApp()
        app.mainloop()
    else:
        sys.exit(main())
