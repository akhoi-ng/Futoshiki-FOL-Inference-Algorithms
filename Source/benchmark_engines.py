#!/usr/bin/env python3
import argparse
import csv
import glob
import io
import json
import os
import statistics
import subprocess
import sys
import time
import tracemalloc
from contextlib import redirect_stdout, redirect_stderr


def parse_args():
    p = argparse.ArgumentParser(description='Benchmark engines with per-case timeout')
    p.add_argument('--inputs', default='Inputs/input-*.txt', help='Glob pattern for input files')
    p.add_argument('--algorithms', nargs='+', default=['fc', 'bt', 'bc', 'astar'],
                   help='Algorithms to run: fc bt bc astar cnf')
    p.add_argument('--heuristic', default='h2', choices=['h1', 'h2', 'h3'], help='A* heuristic')
    p.add_argument('--timeout', type=float, default=30.0, help='Timeout seconds per (input,algo)')
    p.add_argument('--csv', default=None, help='Optional CSV output path')
    p.add_argument('--child', action='store_true', help=argparse.SUPPRESS)
    p.add_argument('--input-file', default=None, help=argparse.SUPPRESS)
    p.add_argument('--algo', default=None, help=argparse.SUPPRESS)
    return p.parse_args()


def run_child(input_file, algo, heuristic):
    from futoshiki import parse_input
    from main import run_solver

    puzzle = parse_input(input_file)

    tracemalloc.start()
    t0 = time.perf_counter()
    # Suppress verbose prints from some engines (e.g., CNF stats)
    with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
        if algo == 'astar':
            solution, stats = run_solver(puzzle, algo, heuristic)
        else:
            solution, stats = run_solver(puzzle, algo)
    elapsed = time.perf_counter() - t0
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    out = {
        'ok': True,
        'solved': bool(solution is not None),
        'time_s': float(stats.get('time', elapsed)) if isinstance(stats, dict) else float(elapsed),
        'nodes': int(stats.get('nodes', -1)) if isinstance(stats, dict) and isinstance(stats.get('nodes', None), (int, float)) else -1,
        'mem_peak_kb': peak / 1024.0,
    }
    print(json.dumps(out, ensure_ascii=True))


def run_parent(args):
    files = sorted(glob.glob(args.inputs))
    files = [f for f in files if os.path.getsize(f) > 0]
    if not files:
        print('No non-empty input files matched.')
        return 1

    rows = []

    for f in files:
        for algo in args.algorithms:
            cmd = [
                sys.executable,
                os.path.abspath(__file__),
                '--child',
                '--input-file', f,
                '--algo', algo,
                '--heuristic', args.heuristic,
            ]
            t0 = time.perf_counter()
            try:
                cp = subprocess.run(cmd, capture_output=True, text=True, timeout=args.timeout)
                wall = time.perf_counter() - t0
                if cp.returncode != 0:
                    rows.append({
                        'input': os.path.basename(f),
                        'algo': algo if algo != 'astar' else f'astar-{args.heuristic}',
                        'status': 'error',
                        'solved': '',
                        'time_s': round(wall, 6),
                        'nodes': '',
                        'mem_peak_kb': '',
                        'note': cp.stderr.strip()[-200:],
                    })
                    continue

                line = cp.stdout.strip().splitlines()[-1] if cp.stdout.strip() else '{}'
                data = json.loads(line)
                rows.append({
                    'input': os.path.basename(f),
                    'algo': algo if algo != 'astar' else f'astar-{args.heuristic}',
                    'status': 'ok',
                    'solved': int(bool(data.get('solved'))),
                    'time_s': round(float(data.get('time_s', wall)), 6),
                    'nodes': int(data.get('nodes', -1)),
                    'mem_peak_kb': round(float(data.get('mem_peak_kb', 0.0)), 2),
                    'note': '',
                })
            except subprocess.TimeoutExpired:
                rows.append({
                    'input': os.path.basename(f),
                    'algo': algo if algo != 'astar' else f'astar-{args.heuristic}',
                    'status': 'timeout',
                    'solved': '',
                    'time_s': round(args.timeout, 6),
                    'nodes': '',
                    'mem_peak_kb': '',
                    'note': f'> {args.timeout}s',
                })

    header = ['input', 'algo', 'status', 'solved', 'time_s', 'nodes', 'mem_peak_kb', 'note']
    print(','.join(header))
    for r in rows:
        print(','.join(str(r[k]) for k in header))

    ok_rows = [r for r in rows if r['status'] == 'ok']
    if ok_rows:
        print('\nAGGREGATE (ok only)')
        print('algo,solved/total,avg_time_s,avg_nodes,avg_mem_peak_kb')
        algos = sorted(set(r['algo'] for r in ok_rows))
        for algo in algos:
            g = [r for r in ok_rows if r['algo'] == algo]
            solved = sum(int(r['solved']) for r in g)
            times = [float(r['time_s']) for r in g]
            nodes = [int(r['nodes']) for r in g if str(r['nodes']) != '']
            mems = [float(r['mem_peak_kb']) for r in g if str(r['mem_peak_kb']) != '']
            avg_nodes = statistics.mean(nodes) if nodes else 0.0
            avg_mems = statistics.mean(mems) if mems else 0.0
            print(f"{algo},{solved}/{len(g)},{statistics.mean(times):.6f},{avg_nodes:.2f},{avg_mems:.2f}")

    if args.csv:
        os.makedirs(os.path.dirname(args.csv) or '.', exist_ok=True)
        with open(args.csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=header)
            writer.writeheader()
            writer.writerows(rows)
        print(f"\nSaved CSV: {args.csv}")

    return 0


def main():
    args = parse_args()
    if args.child:
        if not args.input_file or not args.algo:
            print(json.dumps({'ok': False, 'error': 'missing child args'}))
            return 2
        run_child(args.input_file, args.algo, args.heuristic)
        return 0
    return run_parent(args)


if __name__ == '__main__':
    raise SystemExit(main())
