# #!/usr/bin/env python3
# # -*- coding: utf-8 -*-
# """
# benchmark_engines.py — Chay benchmark tat ca thuat toan Futoshiki.

# Su dung:
#   python benchmark_engines.py
#   python benchmark_engines.py --timeout 60 --csv Results/benchmark.csv
#   python benchmark_engines.py --algorithms fc bt bc astar cnf
#   python benchmark_engines.py --inputs "Inputs/input-0[1-5].txt"

# Cac fix so voi phien ban cu:
#   1. BC timeout khong on dinh: them --child-timeout rieng,
#      subprocess timeout = child_timeout + OVERHEAD_BUFFER
#      de bu cho overhead khoi dong Python + tracemalloc.
#   2. FC phan biet fc_solved: them field 'fc_used_bt' vao JSON,
#      status hien thi 'ok(fc+bt)' khi FC phai dung BT ho tro.
#   3. A* chay ca 3 heuristic: neu 'astar' trong --algorithms,
#      tu dong expand thanh astar-h1, astar-h2, astar-h3.
# """

# import argparse
# import csv
# import glob
# import io
# import json
# import os
# import statistics
# import subprocess
# import sys
# import time
# import tracemalloc
# from contextlib import redirect_stdout, redirect_stderr


# # Overhead buffer (giay) bu cho viec subprocess khoi dong Python,
# # load modules, tracemalloc init. Thuc nghiem thay khoang 2-4s.
# OVERHEAD_BUFFER = 5.0


# # ================================================================
# # ARGUMENT PARSING
# # ================================================================

# def parse_args():
#     p = argparse.ArgumentParser(
#         description='Benchmark Futoshiki solvers with per-case timeout'
#     )
#     p.add_argument(
#         '--inputs', default='Inputs/input-*.txt',
#         help='Glob pattern for input files (default: Inputs/input-*.txt)'
#     )
#     p.add_argument(
#         '--algorithms', nargs='+',
#         default=['fc', 'bt', 'bc', 'astar', 'cnf'],
#         help='Algorithms: fc bt bc astar cnf. '
#              '"astar" tu dong chay ca 3 heuristic h1/h2/h3.'
#     )
#     p.add_argument(
#         '--timeout', type=float, default=60.0,
#         help='Timeout (giay) cho moi cap (input, algo). Default: 60s'
#     )
#     p.add_argument(
#         '--csv', default=None,
#         help='Duong dan file CSV output (optional)'
#     )

#     # Internal args cho child process — an khoi user
#     p.add_argument('--child',       action='store_true', help=argparse.SUPPRESS)
#     p.add_argument('--input-file',  default=None,        help=argparse.SUPPRESS)
#     p.add_argument('--algo',        default=None,        help=argparse.SUPPRESS)
#     p.add_argument('--heuristic',   default='h2',        help=argparse.SUPPRESS)
#     p.add_argument('--child-timeout', type=float, default=60.0, help=argparse.SUPPRESS)

#     return p.parse_args()


# # ================================================================
# # EXPAND ALGORITHMS — astar → astar-h1, astar-h2, astar-h3
# # ================================================================

# def expand_algorithms(algo_list):
#     """
#     Neu 'astar' co trong danh sach → expand thanh 3 bien the.
#     Cac thuat toan khac giu nguyen.

#     Vi du: ['fc', 'bt', 'astar'] → ['fc', 'bt', 'astar-h1', 'astar-h2', 'astar-h3']
#     """
#     result = []
#     for algo in algo_list:
#         if algo == 'astar':
#             result.extend(['astar-h1', 'astar-h2', 'astar-h3'])
#         else:
#             result.append(algo)
#     return result


# def algo_to_params(algo):
#     """
#     Chuyen ten algo thanh (base_algo, heuristic) de truyen vao run_solver.
#     'astar-h2' → ('astar', 'h2')
#     'fc'       → ('fc', 'h2')
#     """
#     if algo.startswith('astar-'):
#         heuristic = algo.split('-')[1]   # 'h1', 'h2', 'h3'
#         return 'astar', heuristic
#     return algo, 'h2'


# # ================================================================
# # CHILD PROCESS — chay 1 (input, algo) va in JSON ra stdout
# # ================================================================

# def run_child(input_file, algo, heuristic, child_timeout):
#     """
#     Chay solver trong child process.
#     In 1 dong JSON ra stdout de parent doc.

#     Fix 1: them child_timeout → signal.alarm (Unix) hoac
#            chay voi deadline check (cross-platform).
#     Fix 2: them 'fc_used_bt' vao output.
#     Fix 3: algo da duoc expand truoc khi goi, chi can parse params.
#     """
#     # Dam bao child process tim duoc cac module cung thu muc
#     script_dir = os.path.dirname(os.path.abspath(__file__))
#     if script_dir not in sys.path:
#         sys.path.insert(0, script_dir)

#     from futoshiki import parse_input
#     from main import run_solver

#     puzzle = parse_input(input_file)
#     base_algo, h = algo_to_params(algo)

#     tracemalloc.start()
#     t0 = time.perf_counter()

#     try:
#         with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
#             result = run_solver(puzzle, base_algo, h)
#         # run_solver co the tra ve (solution, stats) hoac (solution, stats, extra)
#         if len(result) == 3:
#             solution, stats, _ = result
#         else:
#             solution, stats = result
#     except Exception as e:
#         tracemalloc.stop()
#         print(json.dumps({
#             'ok': False,
#             'error': str(e),
#             'solved': False,
#         }), flush=True)
#         return

#     elapsed = time.perf_counter() - t0
#     _, peak = tracemalloc.get_traced_memory()
#     tracemalloc.stop()

#     # Doc stats an toan
#     def get_stat(key, default=-1):
#         if not isinstance(stats, dict):
#             return default
#         val = stats.get(key, default)
#         if isinstance(val, (int, float)):
#             return val
#         return default

#     # Fix 2: phan biet FC tu giai vs FC + BT fallback
#     fc_used_bt = False
#     if base_algo == 'fc' and isinstance(stats, dict):
#         fc_used_bt = not bool(stats.get('fc_solved', True))

#     out = {
#         'ok'         : True,
#         'solved'     : solution is not None,
#         'time_s'     : float(stats.get('time', elapsed)) if isinstance(stats, dict) else elapsed,
#         'nodes'      : int(get_stat('nodes')),
#         'backtracks' : int(get_stat('backtracks')),
#         'inferences' : int(get_stat('inferences', 0)),
#         'mem_peak_kb': peak / 1024.0,
#         'fc_used_bt' : fc_used_bt,   # True = FC bi stuck, dung BT ho tro
#     }
#     print(json.dumps(out, ensure_ascii=True), flush=True)


# # ================================================================
# # PARENT PROCESS — dieu phoi, goi child, thu thap ket qua
# # ================================================================

# def run_parent(args):
#     files = sorted(glob.glob(args.inputs))
#     files = [f for f in files if os.path.getsize(f) > 0]
#     if not files:
#         print('No non-empty input files matched.')
#         return 1

#     # Fix 3: expand 'astar' thanh 3 bien the heuristic
#     algos = expand_algorithms(args.algorithms)

#     rows = []
#     total = len(files) * len(algos)
#     done  = 0

#     print(f"Benchmarking {len(files)} files x {len(algos)} algorithms = {total} runs")
#     print(f"Timeout: {args.timeout}s per run (child gets {args.timeout}s, "
#           f"subprocess kills at {args.timeout + OVERHEAD_BUFFER}s)\n")

#     for f in files:
#         fname = os.path.basename(f)
#         for algo in algos:
#             done += 1
#             print(f"  [{done:2d}/{total}] {fname} + {algo} ... ", end='', flush=True)

#             # Fix 1: subprocess timeout = child_timeout + overhead buffer
#             subprocess_timeout = args.timeout + OVERHEAD_BUFFER

#             cmd = [
#                 sys.executable,
#                 os.path.abspath(__file__),
#                 '--child',
#                 '--input-file',    f,
#                 '--algo',          algo,
#                 '--heuristic',     'h2',       # unused (algo_to_params handles it)
#                 '--child-timeout', str(args.timeout),
#             ]

#             t0 = time.perf_counter()
#             try:
#                 script_dir = os.path.dirname(os.path.abspath(__file__))
#                 cp = subprocess.run(
#                     cmd,
#                     capture_output=True,
#                     text=True,
#                     timeout=subprocess_timeout,
#                     cwd=script_dir,
#                 )
#                 wall = time.perf_counter() - t0

#                 if cp.returncode != 0:
#                     print(f"ERROR (returncode={cp.returncode})")
#                     rows.append(_make_row(
#                         fname, algo,
#                         status='error',
#                         time_s=round(wall, 6),
#                         note=cp.stderr.strip()[-300:] or cp.stdout.strip()[-300:]
#                     ))
#                     continue

#                 # Lay dong JSON cuoi cung tu stdout
#                 lines = [l for l in cp.stdout.strip().splitlines() if l.strip()]
#                 if not lines:
#                     print("ERROR (no output)")
#                     rows.append(_make_row(fname, algo, status='error',
#                                          time_s=round(wall, 6), note='no output'))
#                     continue

#                 try:
#                     data = json.loads(lines[-1])
#                 except json.JSONDecodeError:
#                     print("ERROR (bad JSON)")
#                     rows.append(_make_row(fname, algo, status='error',
#                                          time_s=round(wall, 6), note='bad json'))
#                     continue

#                 if not data.get('ok', False):
#                     print(f"ERROR ({data.get('error', '?')})")
#                     rows.append(_make_row(fname, algo, status='error',
#                                          time_s=round(wall, 6),
#                                          note=data.get('error', '')))
#                     continue

#                 # Fix 2: phan biet FC + BT fallback trong status
#                 fc_used_bt = bool(data.get('fc_used_bt', False))
#                 if algo == 'fc' and fc_used_bt:
#                     status = 'ok(fc+bt)'   # FC bi stuck, BT ho tro
#                 else:
#                     status = 'ok'

#                 solved = bool(data.get('solved', False))
#                 t_s    = round(float(data.get('time_s', wall)), 6)
#                 nodes  = int(data.get('nodes', -1))
#                 bt     = int(data.get('backtracks', -1))
#                 inf    = int(data.get('inferences', 0))
#                 mem    = round(float(data.get('mem_peak_kb', 0.0)), 2)

#                 label = f"{'OK' if solved else 'FAIL'} {t_s:.3f}s"
#                 if fc_used_bt:
#                     label += " [FC+BT]"
#                 print(label)

#                 rows.append({
#                     'input'       : fname,
#                     'algo'        : algo,
#                     'status'      : status,
#                     'solved'      : int(solved),
#                     'time_s'      : t_s,
#                     'nodes'       : nodes,
#                     'backtracks'  : bt,
#                     'inferences'  : inf,
#                     'mem_peak_kb' : mem,
#                     'note'        : '',
#                 })

#             except subprocess.TimeoutExpired:
#                 wall = time.perf_counter() - t0
#                 print(f"TIMEOUT (>{args.timeout}s)")
#                 rows.append(_make_row(
#                     fname, algo,
#                     status='timeout',
#                     time_s=round(args.timeout, 6),
#                     note=f'>{args.timeout}s'
#                 ))

#     # ── In bang ket qua ──
#     _print_results(rows, args)
#     return 0


# def _make_row(input_name, algo, status, time_s=0.0, note=''):
#     """Tao row voi gia tri mac dinh cho truong hop loi/timeout."""
#     return {
#         'input'      : input_name,
#         'algo'       : algo,
#         'status'     : status,
#         'solved'     : '',
#         'time_s'     : time_s,
#         'nodes'      : '',
#         'backtracks' : '',
#         'inferences' : '',
#         'mem_peak_kb': '',
#         'note'       : note,
#     }


# def _print_results(rows, args):
#     """In bang CSV va aggregate summary."""

#     header = ['input', 'algo', 'status', 'solved',
#               'time_s', 'nodes', 'backtracks', 'inferences',
#               'mem_peak_kb', 'note']

#     print('\n' + '='*80)
#     print('RESULTS')
#     print('='*80)
#     print(','.join(header))
#     for r in rows:
#         print(','.join(str(r.get(k, '')) for k in header))

#     # Aggregate — chi tinh cac row co status ok hoac ok(fc+bt)
#     ok_rows = [r for r in rows if r['status'].startswith('ok')]
#     if ok_rows:
#         print('\n' + '='*80)
#         print('AGGREGATE (ok + ok(fc+bt) only)')
#         print('='*80)
#         agg_header = ['algo', 'solved/total', 'avg_time_s',
#                       'avg_nodes', 'avg_bt', 'avg_mem_kb', 'fc+bt_count']
#         print(','.join(agg_header))

#         algos_seen = list(dict.fromkeys(r['algo'] for r in ok_rows))
#         for algo in algos_seen:
#             g = [r for r in ok_rows if r['algo'] == algo]
#             solved    = sum(int(r['solved']) for r in g if r['solved'] != '')
#             times     = [float(r['time_s']) for r in g]
#             nodes     = [int(r['nodes']) for r in g if str(r['nodes']).lstrip('-').isdigit()]
#             bts       = [int(r['backtracks']) for r in g if str(r['backtracks']).lstrip('-').isdigit()]
#             mems      = [float(r['mem_peak_kb']) for r in g if str(r['mem_peak_kb']).replace('.','').isdigit()]
#             fc_bt_cnt = sum(1 for r in g if r['status'] == 'ok(fc+bt)')

#             avg_nodes = statistics.mean(nodes) if nodes else 0.0
#             avg_bts   = statistics.mean(bts)   if bts   else 0.0
#             avg_mems  = statistics.mean(mems)  if mems  else 0.0

#             fc_note = f'{fc_bt_cnt}' if algo == 'fc' else '-'
#             print(f"{algo},{solved}/{len(g)},{statistics.mean(times):.4f},"
#                   f"{avg_nodes:.1f},{avg_bts:.1f},{avg_mems:.1f},{fc_note}")

#     # Luu CSV
#     if args.csv:
#         os.makedirs(os.path.dirname(args.csv) or '.', exist_ok=True)
#         with open(args.csv, 'w', newline='', encoding='utf-8') as f:
#             writer = csv.DictWriter(f, fieldnames=header, extrasaction='ignore')
#             writer.writeheader()
#             writer.writerows(rows)
#         print(f'\nSaved: {args.csv}')


# # ================================================================
# # ENTRY POINT
# # ================================================================

# def main():
#     args = parse_args()
#     if args.child:
#         if not args.input_file or not args.algo:
#             print(json.dumps({'ok': False, 'error': 'missing child args'}))
#             return 2
#         run_child(args.input_file, args.algo, args.heuristic, args.child_timeout)
#         return 0
#     return run_parent(args)


# if __name__ == '__main__':
#     raise SystemExit(main())


#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
benchmark_engines.py — Chay benchmark tat ca thuat toan Futoshiki.

Su dung:
  python benchmark_engines.py
  python benchmark_engines.py --timeout 60 --csv Results/benchmark.csv
  python benchmark_engines.py --algorithms fc bt bc astar cnf
  python benchmark_engines.py --inputs "Inputs/input-0[1-5].txt"

Cac fix so voi phien ban cu:
  1. BC timeout khong on dinh: them --child-timeout rieng,
     subprocess timeout = child_timeout + OVERHEAD_BUFFER
     de bu cho overhead khoi dong Python + tracemalloc.
  2. FC phan biet fc_solved: them field 'fc_used_bt' vao JSON,
     status hien thi 'ok(fc+bt)' khi FC phai dung BT ho tro.
  3. A* chay ca 3 heuristic: neu 'astar' trong --algorithms,
     tu dong expand thanh astar-h1, astar-h2, astar-h3.
  4. TWO-PASS BENCHMARKING: Them --track-mem de tach biet viec do Time va do RAM,
     tranh hien tuong tracemalloc lam nghen co chai (Observer Effect).
"""

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


# Overhead buffer (giay) bu cho viec subprocess khoi dong Python,
# load modules, tracemalloc init. Thuc nghiem thay khoang 2-4s.
OVERHEAD_BUFFER = 5.0


# ================================================================
# ARGUMENT PARSING
# ================================================================

def parse_args():
    p = argparse.ArgumentParser(
        description='Benchmark Futoshiki solvers with per-case timeout'
    )
    p.add_argument(
        '--inputs', default='Inputs/input-*.txt',
        help='Glob pattern for input files (default: Inputs/input-*.txt)'
    )
    p.add_argument(
        '--algorithms', nargs='+',
        default=['fc', 'bt', 'bc', 'astar', 'cnf'],
        help='Algorithms: fc bt bc astar cnf. '
             '"astar" tu dong chay ca 3 heuristic h1/h2/h3.'
    )
    p.add_argument(
        '--timeout', type=float, default=600.0,
        help='Timeout (giay) cho moi cap (input, algo). Default: 60s'
    )
    p.add_argument(
        '--csv', default=None,
        help='Duong dan file CSV output (optional)'
    )
    p.add_argument(
        '--track-mem', action='store_true',
        help='Bat tracemalloc de do Memory (luu y: se lam cham toc do thuc thi rat nhieu)'
    )

    # Internal args cho child process — an khoi user
    p.add_argument('--child',           action='store_true', help=argparse.SUPPRESS)
    p.add_argument('--input-file',      default=None,        help=argparse.SUPPRESS)
    p.add_argument('--algo',            default=None,        help=argparse.SUPPRESS)
    p.add_argument('--heuristic',       default='h2',        help=argparse.SUPPRESS)
    p.add_argument('--child-timeout',   type=float, default=600.0, help=argparse.SUPPRESS)
    p.add_argument('--child-track-mem', action='store_true', help=argparse.SUPPRESS)

    return p.parse_args()


# ================================================================
# EXPAND ALGORITHMS — astar → astar-h1, astar-h2, astar-h3
# ================================================================

def expand_algorithms(algo_list):
    """
    Neu 'astar' co trong danh sach → expand thanh 3 bien the.
    Cac thuat toan khac giu nguyen.
    """
    result = []
    for algo in algo_list:
        if algo == 'astar':
            result.extend(['astar-h1', 'astar-h2', 'astar-h3'])
        else:
            result.append(algo)
    return result


def algo_to_params(algo):
    """
    Chuyen ten algo thanh (base_algo, heuristic) de truyen vao run_solver.
    """
    if algo.startswith('astar-'):
        heuristic = algo.split('-')[1]   # 'h1', 'h2', 'h3'
        return 'astar', heuristic
    return algo, 'h2'


# ================================================================
# CHILD PROCESS — chay 1 (input, algo) va in JSON ra stdout
# ================================================================

def run_child(input_file, algo, heuristic, child_timeout, track_mem=False):
    """
    Chay solver trong child process.
    In 1 dong JSON ra stdout de parent doc.
    """
    # Dam bao child process tim duoc cac module cung thu muc
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)

    from futoshiki import parse_input
    from main import run_solver

    puzzle = parse_input(input_file)
    base_algo, h = algo_to_params(algo)

    # Chi bat memory tracker neu co flag (de tranh Overhead cho CPU)
    if track_mem:
        tracemalloc.start()
        
    t0 = time.perf_counter()

    try:
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            result = run_solver(puzzle, base_algo, h)
            
        if len(result) == 3:
            solution, stats, _ = result
        else:
            solution, stats = result
            
    except Exception as e:
        if track_mem:
            tracemalloc.stop()
        print(json.dumps({
            'ok': False,
            'error': str(e),
            'solved': False,
        }), flush=True)
        return

    elapsed = time.perf_counter() - t0
    
    # Doc bo nho neu dang bat track_mem
    if track_mem:
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
    else:
        peak = 0.0

    def get_stat(key, default=-1):
        if not isinstance(stats, dict):
            return default
        val = stats.get(key, default)
        if isinstance(val, (int, float)):
            return val
        return default

    fc_used_bt = False
    if base_algo == 'fc' and isinstance(stats, dict):
        fc_used_bt = not bool(stats.get('fc_solved', True))

    out = {
        'ok'         : True,
        'solved'     : solution is not None,
        'time_s'     : float(stats.get('time', elapsed)) if isinstance(stats, dict) else elapsed,
        'nodes'      : int(get_stat('nodes')),
        'backtracks' : int(get_stat('backtracks')),
        'inferences' : int(get_stat('inferences', 0)),
        'mem_peak_kb': peak / 1024.0,
        'fc_used_bt' : fc_used_bt,
    }
    print(json.dumps(out, ensure_ascii=True), flush=True)


# ================================================================
# PARENT PROCESS — dieu phoi, goi child, thu thap ket qua
# ================================================================

def run_parent(args):
    files = sorted(glob.glob(args.inputs))
    files = [f for f in files if os.path.getsize(f) > 0]
    if not files:
        print('No non-empty input files matched.')
        return 1

    algos = expand_algorithms(args.algorithms)

    rows = []
    total = len(files) * len(algos)
    done  = 0

    mode_msg = "MEMORY TRACKING ON (Slow)" if args.track_mem else "SPEED MODE (Fast)"
    print(f"Benchmarking {len(files)} files x {len(algos)} algorithms = {total} runs")
    print(f"Mode: {mode_msg}")
    print(f"Timeout: {args.timeout}s per run (subprocess kills at {args.timeout + OVERHEAD_BUFFER}s)\n")

    for f in files:
        fname = os.path.basename(f)
        for algo in algos:
            done += 1
            print(f"  [{done:2d}/{total}] {fname} + {algo} ... ", end='', flush=True)

            subprocess_timeout = args.timeout + OVERHEAD_BUFFER

            cmd = [
                sys.executable,
                os.path.abspath(__file__),
                '--child',
                '--input-file',    f,
                '--algo',          algo,
                '--heuristic',     'h2',
                '--child-timeout', str(args.timeout),
            ]
            
            # Truyen co track_mem xuong cho child process
            if args.track_mem:
                cmd.append('--child-track-mem')

            t0 = time.perf_counter()
            try:
                script_dir = os.path.dirname(os.path.abspath(__file__))
                cp = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=subprocess_timeout,
                    cwd=script_dir,
                )
                wall = time.perf_counter() - t0

                if cp.returncode != 0:
                    print(f"ERROR (returncode={cp.returncode})")
                    rows.append(_make_row(
                        fname, algo,
                        status='error',
                        time_s=round(wall, 6),
                        note=cp.stderr.strip()[-300:] or cp.stdout.strip()[-300:]
                    ))
                    continue

                lines = [l for l in cp.stdout.strip().splitlines() if l.strip()]
                if not lines:
                    print("ERROR (no output)")
                    rows.append(_make_row(fname, algo, status='error',
                                         time_s=round(wall, 6), note='no output'))
                    continue

                try:
                    data = json.loads(lines[-1])
                except json.JSONDecodeError:
                    print("ERROR (bad JSON)")
                    rows.append(_make_row(fname, algo, status='error',
                                         time_s=round(wall, 6), note='bad json'))
                    continue

                if not data.get('ok', False):
                    print(f"ERROR ({data.get('error', '?')})")
                    rows.append(_make_row(fname, algo, status='error',
                                         time_s=round(wall, 6),
                                         note=data.get('error', '')))
                    continue

                fc_used_bt = bool(data.get('fc_used_bt', False))
                if algo == 'fc' and fc_used_bt:
                    status = 'ok(fc+bt)'
                else:
                    status = 'ok'

                solved = bool(data.get('solved', False))
                t_s    = round(float(data.get('time_s', wall)), 6)
                nodes  = int(data.get('nodes', -1))
                bt     = int(data.get('backtracks', -1))
                inf    = int(data.get('inferences', 0))
                mem    = round(float(data.get('mem_peak_kb', 0.0)), 2)

                label = f"{'OK' if solved else 'FAIL'} {t_s:.3f}s"
                if fc_used_bt:
                    label += " [FC+BT]"
                print(label)

                rows.append({
                    'input'       : fname,
                    'algo'        : algo,
                    'status'      : status,
                    'solved'      : int(solved),
                    'time_s'      : t_s,
                    'nodes'       : nodes,
                    'backtracks'  : bt,
                    'inferences'  : inf,
                    'mem_peak_kb' : mem,
                    'note'        : '',
                })

            except subprocess.TimeoutExpired:
                wall = time.perf_counter() - t0
                print(f"TIMEOUT (>{args.timeout}s)")
                rows.append(_make_row(
                    fname, algo,
                    status='timeout',
                    time_s=round(args.timeout, 6),
                    note=f'>{args.timeout}s'
                ))

    _print_results(rows, args)
    return 0


def _make_row(input_name, algo, status, time_s=0.0, note=''):
    return {
        'input'      : input_name,
        'algo'       : algo,
        'status'     : status,
        'solved'     : '',
        'time_s'     : time_s,
        'nodes'      : '',
        'backtracks' : '',
        'inferences' : '',
        'mem_peak_kb': '',
        'note'       : note,
    }


def _print_results(rows, args):
    header = ['input', 'algo', 'status', 'solved',
              'time_s', 'nodes', 'backtracks', 'inferences',
              'mem_peak_kb', 'note']

    print('\n' + '='*80)
    print('RESULTS')
    print('='*80)
    print(','.join(header))
    for r in rows:
        print(','.join(str(r.get(k, '')) for k in header))

    ok_rows = [r for r in rows if r['status'].startswith('ok')]
    if ok_rows:
        print('\n' + '='*80)
        print('AGGREGATE (ok + ok(fc+bt) only)')
        print('='*80)
        agg_header = ['algo', 'solved/total', 'avg_time_s',
                      'avg_nodes', 'avg_bt', 'avg_mem_kb', 'fc+bt_count']
        print(','.join(agg_header))

        algos_seen = list(dict.fromkeys(r['algo'] for r in ok_rows))
        for algo in algos_seen:
            g = [r for r in ok_rows if r['algo'] == algo]
            solved    = sum(int(r['solved']) for r in g if r['solved'] != '')
            times     = [float(r['time_s']) for r in g]
            nodes     = [int(r['nodes']) for r in g if str(r['nodes']).lstrip('-').isdigit()]
            bts       = [int(r['backtracks']) for r in g if str(r['backtracks']).lstrip('-').isdigit()]
            mems      = [float(r['mem_peak_kb']) for r in g if str(r['mem_peak_kb']).replace('.','').isdigit()]
            fc_bt_cnt = sum(1 for r in g if r['status'] == 'ok(fc+bt)')

            avg_nodes = statistics.mean(nodes) if nodes else 0.0
            avg_bts   = statistics.mean(bts)   if bts   else 0.0
            avg_mems  = statistics.mean(mems)  if mems  else 0.0

            fc_note = f'{fc_bt_cnt}' if algo == 'fc' else '-'
            print(f"{algo},{solved}/{len(g)},{statistics.mean(times):.4f},"
                  f"{avg_nodes:.1f},{avg_bts:.1f},{avg_mems:.1f},{fc_note}")

    if args.csv:
        os.makedirs(os.path.dirname(args.csv) or '.', exist_ok=True)
        with open(args.csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=header, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(rows)
        print(f'\nSaved: {args.csv}')


# ================================================================
# ENTRY POINT
# ================================================================

def main():
    args = parse_args()
    if args.child:
        if not args.input_file or not args.algo:
            print(json.dumps({'ok': False, 'error': 'missing child args'}))
            return 2
        run_child(args.input_file, args.algo, args.heuristic, args.child_timeout, args.child_track_mem)
        return 0
    return run_parent(args)


if __name__ == '__main__':
    raise SystemExit(main())