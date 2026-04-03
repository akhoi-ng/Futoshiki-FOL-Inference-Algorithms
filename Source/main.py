#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Futoshiki Solver - Main Entry Point
CSC14003 - Artificial Intelligence
"""

import sys
import argparse
import time
from pathlib import Path

from futoshiki import parse_input, build_initial_assignment
from forward_chain import solve_forward_chaining
from backtracking import solve_backtracking
from display import print_header, format_grid, format_statistics, save_solution


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Giai Futoshiki puzzle bang cac thuat toan FOL inference',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Vi du:
  python main.py Inputs/input-01.txt fc
  python main.py Inputs/input-01.txt bt Outputs/output-01.txt
        """
    )
    
    parser.add_argument('input_file', help='Duong dan den file input chua puzzle')
    parser.add_argument('algorithm', choices=['fc', 'bt', 'bc', 'astar', 'cnf'],
                       help='Thuat toan su dung: fc (Forward Chaining), bt (Backtracking)')
    parser.add_argument('output_file', nargs='?', default=None,
                       help='Duong dan file output (optional)')
    
    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_arguments()
    
    # Check file exists
    input_path = Path(args.input_file)
    if not input_path.exists():
        print(f"Loi: Khong tim thay file '{args.input_file}'")
        print(f"Duong dan tuyet doi: {input_path.absolute()}")
        sys.exit(1)
    
    algo_names = {
        'fc': 'Forward Chaining',
        'bt': 'Backtracking',
        'bc': 'Backward Chaining',
        'astar': 'A* Search',
        'cnf': 'CNF Generator'
    }
    
    algo_name = algo_names.get(args.algorithm, args.algorithm.upper())
    
    try:
        # Load puzzle
        print(f"Dang doc puzzle tu: {args.input_file}")
        puzzle = parse_input(str(input_path))
        initial_assignment = build_initial_assignment(puzzle)
        
        print_header(algo_name, args.input_file, puzzle.N)
        
        print("\nTrang thai ban dau:")
        print(format_grid(puzzle, initial_assignment))
        print("\nDang giai...")
        
        # Route to algorithm
        start_time = time.time()
        solution = None
        stats = {}
        
        if args.algorithm == 'fc':
            solution, stats = solve_forward_chaining(puzzle)
        elif args.algorithm == 'bt':
            solution, stats = solve_backtracking(puzzle)
        elif args.algorithm in ['bc', 'astar', 'cnf']:
            print(f"Loi: {algo_name} chua duoc implement")
            sys.exit(1)
        
        end_time = time.time()
        stats['time'] = end_time - start_time
        
        # Display results
        if solution:
            print("\nTim thay loi giai!\n")
            print(format_grid(puzzle, solution))
            print(format_statistics(stats))
            
            if args.output_file:
                output_path = Path(args.output_file)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                save_solution(solution, puzzle.N, str(output_path))
                print(f"\nDa luu ket qua vao: {args.output_file}")
            
            print("\n" + "="*60)
            return 0
        else:
            print("\nKhong tim thay loi giai!")
            print(format_statistics(stats))
            print("\n" + "="*60)
            return 1
            
    except FileNotFoundError as e:
        print(f"Loi: Khong tim thay file - {e}")
        return 1
    except ValueError as e:
        print(f"Loi: Du lieu khong hop le - {e}")
        return 1
    except Exception as e:
        print(f"Loi khong mong doi: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
