#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gui.py — Futoshiki Solver GUI
CSC14003 - Co so Tri tue Nhan tao

Chay: python main.py  (khong can arguments)
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
import threading
import queue
import time
import os
import sys
import traceback
from collections import deque

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from futoshiki import parse_input, build_initial_assignment
from main import run_solver, ALGO_NAMES

# ================================================================
# COLORS — Tokyo Night inspired dark theme
# ================================================================
C = {
    'bg':        '#1a1b26',
    'surface':   '#24283b',
    'surface2':  '#292e42',
    'primary':   '#7aa2f7',
    'secondary': '#9ece6a',
    'accent':    '#ff9e64',
    'text':      '#c0caf5',
    'text_dim':  '#565f89',
    'error':     '#f7768e',
    'success':   '#9ece6a',
    'warning':   '#e0af68',
    'border':    '#3b4261',
    'cell_bg':   '#1f2335',
}

ALGO_OPTIONS = [
    ('Forward Chaining', 'fc'),
    ('Backtracking', 'bt'),
    ('Backward Chaining', 'bc'),
    ('A* Search', 'astar'),
    ('CNF Generator', 'cnf'),
]

HEURISTIC_OPTIONS = [
    ('H1 - Trivial', 'h1'),
    ('H2 - Domain Wipeout', 'h2'),
    ('H3 - AC-3', 'h3'),
]


class StopSolverException(Exception):
    pass


# ================================================================
# FUTOSHIKI GRID CANVAS
# ================================================================

class FutoshikiCanvas(tk.Canvas):
    """Custom Canvas to draw Futoshiki grid with constraints."""

    def __init__(self, master, cell_size=52, con_gap=20, padding=12, **kw):
        self._cs = cell_size
        self._cg = con_gap
        self._pad = padding
        super().__init__(master, bg=C['surface'], highlightthickness=0, bd=0, **kw)
        self.puzzle = None
        self.assignment = {}
        self.initial_assignment = {}
        self.hi_cell = None
        self.hi_color = None
        
        # Dictionaries to store Tkinter item IDs so we can update them without recreating
        self._rect_ids = {}   
        self._text_ids = {}
        self._grid_drawn = False

    def set_puzzle(self, puzzle):
        self.puzzle = puzzle
        self.initial_assignment = build_initial_assignment(puzzle)
        self.assignment = dict(self.initial_assignment)
        N = puzzle.N
        w = N * self._cs + (N - 1) * self._cg + 2 * self._pad
        self.configure(width=w, height=w)
        
        # Create all canvas items ONCE
        self._create_grid_items()
        
        self.draw()

    def update_state(self, assignment, hi_cell=None, hi_color=None):
        self.assignment = dict(assignment) if assignment else {}
        self.hi_cell = hi_cell
        self.hi_color = hi_color
        self.draw()

    def clear_solution(self):
        self.assignment = dict(self.initial_assignment)
        self.hi_cell = None
        self.hi_color = None
        self.draw()

    def _xy(self, r, c):
        x = self._pad + c * (self._cs + self._cg)
        y = self._pad + r * (self._cs + self._cg)
        return x, y

    def _rounded_rect(self, x1, y1, x2, y2, r=8, **kw):
        pts = [x1+r,y1, x2-r,y1, x2,y1, x2,y1+r, x2,y2-r, x2,y2,
               x2-r,y2, x1+r,y2, x1,y2, x1,y2-r, x1,y1+r, x1,y1]
        return self.create_polygon(pts, smooth=True, **kw)

    def _create_grid_items(self):
        """Creates the permanent UI elements (rectangles, text shells, constraints) once."""
        self.delete("all")
        self._rect_ids.clear()
        self._text_ids.clear()
        if not self.puzzle:
            return
            
        N = self.puzzle.N
        for r in range(N):
            for c in range(N):
                x, y = self._xy(r, c)
                
                # 1. Create Rectangle and store its ID
                r_id = self._rounded_rect(x, y, x+self._cs, y+self._cs,
                                          fill=C['cell_bg'], outline=C['border'], width=1)
                self._rect_ids[(r, c)] = r_id
                
                # 2. Create Text Placeholder and store its ID (start empty)
                t_id = self.create_text(x + self._cs/2, y + self._cs/2,
                                        text="", font=('Segoe UI', 16, 'normal'), fill=C['secondary'])
                self._text_ids[(r, c)] = t_id

                # 3. Draw static Constraints (we don't need to save IDs because they never change)
                if c < N - 1:
                    con = self.puzzle.h_con[r][c]
                    if con != 0:
                        cx = x + self._cs + self._cg / 2
                        cy = y + self._cs / 2
                        sym = '<' if con == 1 else '>'
                        self.create_text(cx, cy, text=sym,
                                         font=('Segoe UI', 13, 'bold'),
                                         fill=C['accent'])
                if r < N - 1:
                    con = self.puzzle.v_con[r][c]
                    if con != 0:
                        cx = x + self._cs / 2
                        cy = y + self._cs + self._cg / 2
                        sym = '\u2227' if con == 1 else '\u2228'
                        self.create_text(cx, cy, text=sym,
                                         font=('Segoe UI', 11, 'bold'),
                                         fill=C['accent'])
        self._grid_drawn = True

    def draw(self):
        """Updates the attributes of existing items instead of deleting/redrawing."""
        if not self.puzzle or not self._grid_drawn:
            return
            
        N = self.puzzle.N

        for r in range(N):
            for c in range(N):
                is_hi = self.hi_cell == (r, c)

                # --- 1. Update Rectangle Attributes ---
                if is_hi and self.hi_color == 'backtrack':
                    bg, brd = '#3b2229', C['error']
                elif is_hi and self.hi_color == 'assign':
                    bg, brd = '#1a2e1a', C['success']
                elif is_hi:
                    bg, brd = '#283457', C['primary']
                else:
                    bg, brd = C['cell_bg'], C['border']

                self.itemconfig(self._rect_ids[(r, c)], fill=bg, outline=brd, 
                                width=2 if is_hi else 1)

                # --- 2. Update Text Attributes ---
                val = self.assignment.get((r, c))
                is_init = (r, c) in self.initial_assignment
                
                if val is None:
                    # Clear cell if it has no assignment
                    self.itemconfig(self._text_ids[(r, c)], text="")
                else:
                    if is_hi and self.hi_color == 'backtrack':
                        clr = C['error']
                    elif is_hi and self.hi_color == 'assign':
                        clr = C['success']
                    elif is_init:
                        clr = C['text']
                    else:
                        clr = C['secondary']
                        
                    fw = 'bold' if is_init else 'normal'
                    
                    self.itemconfig(self._text_ids[(r, c)], 
                                    text=str(val), 
                                    fill=clr, 
                                    font=('Segoe UI', 16, fw))


# ================================================================
# MAIN APPLICATION
# ================================================================

class FutoshikiApp(ctk.CTk):

    def __init__(self):
        super().__init__()
        self.title("\U0001f9e9 Futoshiki Solver")
        self.geometry("1260x800")
        self.minsize(1060, 680)
        
        # Maximize window on startup (zoomed for Windows)
        self.after(0, lambda: self.state('zoomed'))
        
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.puzzle = None
        self.solver_thread = None
        self.stop_event = threading.Event()
        self.pause_event = threading.Event()
        self.pause_event.set()
        self.step_queue = queue.Queue()
        self.step_delay_ms = 50
        self.use_delay = tk.BooleanVar(value=True)
        self.step_count = 0
        self.solving = False
        self._pending_steps = deque()

        self._build_ui()

    # ────────────────────────────────────────────────────────────
    # BUILD UI
    # ────────────────────────────────────────────────────────────

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=0, minsize=255)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)

        self._build_header()
        self._build_left()
        self._build_right()

    def _build_header(self):
        hdr = ctk.CTkFrame(self, height=48, corner_radius=0, fg_color=C['surface'])
        hdr.grid(row=0, column=0, columnspan=2, sticky="ew")
        hdr.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(hdr, text="\U0001f9e9 FUTOSHIKI SOLVER",
                     font=ctk.CTkFont(size=18, weight="bold"),
                     text_color=C['primary']).grid(row=0, column=0, padx=16, pady=8, sticky="w")
        ctk.CTkLabel(hdr, text="FOL Inference Algorithms",
                     font=ctk.CTkFont(size=11),
                     text_color=C['text_dim']).grid(row=0, column=1, padx=16, pady=8, sticky="e")

    def _build_left(self):
        left = ctk.CTkFrame(self, width=255, corner_radius=0, fg_color=C['bg'])
        left.grid(row=1, column=0, sticky="nsew")
        left.grid_propagate(False)

        # ── File section ──
        sec = ctk.CTkFrame(left, fg_color=C['surface'], corner_radius=10)
        sec.pack(fill="x", padx=8, pady=(8, 4))
        ctk.CTkLabel(sec, text="\U0001f4c2 INPUT FILE",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=C['text_dim']).pack(padx=12, pady=(8, 4), anchor="w")
        self.file_btn = ctk.CTkButton(sec, text="Chọn file input...",
                                       command=self._browse_file,
                                       fg_color=C['surface2'], hover_color=C['border'],
                                       border_color=C['border'], border_width=1, height=32)
        self.file_btn.pack(fill="x", padx=12, pady=4)
        self.file_info = ctk.CTkLabel(sec, text="Chưa chọn file",
                                       font=ctk.CTkFont(size=10),
                                       text_color=C['text_dim'], wraplength=220)
        self.file_info.pack(padx=12, pady=(0, 8), anchor="w")

        # ── Algorithm section ──
        sec2 = ctk.CTkFrame(left, fg_color=C['surface'], corner_radius=10)
        sec2.pack(fill="x", padx=8, pady=4)
        ctk.CTkLabel(sec2, text="\u2699 THUẬT TOÁN",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=C['text_dim']).pack(padx=12, pady=(8, 4), anchor="w")

        self.algo_var = tk.StringVar(value="bt")
        for label, key in ALGO_OPTIONS:
            ctk.CTkRadioButton(sec2, text=label, variable=self.algo_var, value=key,
                               font=ctk.CTkFont(size=11), command=self._on_algo_change,
                               fg_color=C['primary'], hover_color=C['primary']
                               ).pack(padx=16, pady=2, anchor="w")

        # Heuristic submenu — always present, visibility toggled
        self.h_frame = ctk.CTkFrame(sec2, fg_color='transparent', height=30)
        self.h_frame.pack(fill="x", padx=28, pady=(0, 4))
        self.h_frame.pack_propagate(False)
        self.h_label_w = ctk.CTkLabel(self.h_frame, text="Heuristic:",
                                       font=ctk.CTkFont(size=10),
                                       text_color=C['text_dim'])
        self.h_var = tk.StringVar(value="h2")
        self.h_menu = ctk.CTkOptionMenu(
            self.h_frame, variable=self.h_var,
            values=[l for l, _ in HEURISTIC_OPTIONS],
            width=140, height=24, font=ctk.CTkFont(size=10),
            fg_color=C['surface2'], button_color=C['border'],
            command=self._on_heuristic_change)
        # Hidden by default (not A*) — children not packed
        ctk.CTkLabel(sec2, text="").pack(pady=1)

        # ── Actions ──
        sec3 = ctk.CTkFrame(left, fg_color=C['surface'], corner_radius=10)
        sec3.pack(fill="x", padx=8, pady=4)

        self.solve_btn = ctk.CTkButton(
            sec3, text="\u25B6  GIẢI", command=self._start_solving,
            fg_color=C['primary'], hover_color='#5d8ae6',
            font=ctk.CTkFont(size=13, weight="bold"), height=38)
        self.solve_btn.pack(fill="x", padx=12, pady=(8, 4))

        action_row = ctk.CTkFrame(sec3, fg_color='transparent')
        action_row.pack(fill="x", padx=12, pady=4)

        self.pause_btn = ctk.CTkButton(
            action_row, text="\u23f8 TẠM DỪNG", command=self._toggle_pause,
            fg_color=C['warning'], hover_color='#e6b973', text_color='#1a1b26',
            font=ctk.CTkFont(size=11, weight="bold"), height=32, state="disabled", width=105)
        self.pause_btn.pack(side="left", fill="x", expand=True, padx=(0, 4))

        self.stop_btn = ctk.CTkButton(
            action_row, text="\u23F9 DỪNG HẲN", command=self._stop_solving,
            fg_color=C['error'], hover_color='#d45a6e',
            font=ctk.CTkFont(size=11, weight="bold"), height=32, state="disabled", width=105)
        self.stop_btn.pack(side="right", fill="x", expand=True, padx=(4, 0))

        self.delay_sw = ctk.CTkSwitch(
            sec3, text="Hiển thị từng bước", variable=self.use_delay,
            font=ctk.CTkFont(size=10), fg_color=C['border'],
            progress_color=C['primary'])
        self.delay_sw.pack(padx=12, pady=4, anchor="w")

        spd = ctk.CTkFrame(sec3, fg_color='transparent')
        spd.pack(fill="x", padx=12, pady=(0, 8))
        ctk.CTkLabel(spd, text="Tốc độ:", font=ctk.CTkFont(size=10),
                     text_color=C['text_dim']).pack(side="left")
        self.speed_sl = ctk.CTkSlider(spd, from_=0, to=500, number_of_steps=50,
                                       width=110, fg_color=C['border'],
                                       progress_color=C['primary'],
                                       command=self._on_speed)
        self.speed_sl.set(50)
        self.speed_sl.pack(side="left", padx=4)
        self.speed_lbl = ctk.CTkLabel(spd, text="50ms", font=ctk.CTkFont(size=10),
                                       text_color=C['text_dim'], width=40)
        self.speed_lbl.pack(side="left")

        ctk.CTkFrame(left, fg_color='transparent').pack(fill="both", expand=True)

    def _build_right(self):
        right = ctk.CTkFrame(self, corner_radius=0, fg_color=C['bg'])
        right.grid(row=1, column=1, sticky="nsew")
        right.grid_rowconfigure(0, weight=0)
        right.grid_rowconfigure(1, weight=1)
        right.grid_columnconfigure(0, weight=1)

        # ── Grid section ──
        gsec = ctk.CTkFrame(right, fg_color=C['surface'], corner_radius=10)
        gsec.grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 4))
        inner = ctk.CTkFrame(gsec, fg_color='transparent')
        inner.pack(pady=8, padx=8)

        f1 = ctk.CTkFrame(inner, fg_color='transparent')
        f1.pack(side="left", padx=(8, 4))
        ctk.CTkLabel(f1, text="TRẠNG THÁI BAN ĐẦU",
                     font=ctk.CTkFont(size=10, weight="bold"),
                     text_color=C['text_dim']).pack(pady=(0, 4))
        self.grid_init = FutoshikiCanvas(f1)
        self.grid_init.pack()

        ctk.CTkLabel(inner, text="\u2192",
                     font=ctk.CTkFont(size=26, weight="bold"),
                     text_color=C['text_dim']).pack(side="left", padx=12)

        f2 = ctk.CTkFrame(inner, fg_color='transparent')
        f2.pack(side="left", padx=(4, 8))
        ctk.CTkLabel(f2, text="QUÁ TRÌNH / KẾT QUẢ",
                     font=ctk.CTkFont(size=10, weight="bold"),
                     text_color=C['text_dim']).pack(pady=(0, 4))
        self.grid_sol = FutoshikiCanvas(f2)
        self.grid_sol.pack()

        # ── Bottom: Log + Stats ──
        bot = ctk.CTkFrame(right, fg_color='transparent')
        bot.grid(row=1, column=0, sticky="nsew", padx=8, pady=(4, 8))
        bot.grid_columnconfigure(0, weight=3)
        bot.grid_columnconfigure(1, weight=1)
        bot.grid_rowconfigure(0, weight=1)

        # Log
        lf = ctk.CTkFrame(bot, fg_color=C['surface'], corner_radius=10)
        lf.grid(row=0, column=0, sticky="nsew", padx=(0, 4))
        ctk.CTkLabel(lf, text="\U0001f4cb QUÁ TRÌNH GIẢI",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=C['text_dim']).pack(padx=12, pady=(8, 4), anchor="w")
        self.log = ctk.CTkTextbox(lf, font=ctk.CTkFont(family="Consolas", size=11),
                                   fg_color=C['cell_bg'], text_color=C['text'],
                                   corner_radius=6, wrap="word")
        self.log.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self.log.configure(state="disabled")

        # Stats
        sf = ctk.CTkFrame(bot, fg_color=C['surface'], corner_radius=10)
        sf.grid(row=0, column=1, sticky="nsew", padx=(4, 0))
        ctk.CTkLabel(sf, text="\U0001f4ca THỐNG KÊ",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=C['text_dim']).pack(padx=12, pady=(8, 4), anchor="w")

        self.stat_lbls = {}
        for key, label in [('status','Trạng thái'), ('time','Thời gian'),
                           ('nodes','Nodes'), ('backtracks','Backtracks'),
                           ('inferences','Inferences'), ('iterations','Iterations'),
                           ('memory','Memory'), ('heuristic','Heuristic'),
                           ('cnf_vars','CNF Vars'), ('cnf_clauses','CNF Clauses')]:
            row = ctk.CTkFrame(sf, fg_color='transparent')
            row.pack(fill="x", padx=12, pady=1)
            ctk.CTkLabel(row, text=f"{label}:", font=ctk.CTkFont(size=10),
                         text_color=C['text_dim'], width=75, anchor="w").pack(side="left")
            v = ctk.CTkLabel(row, text="—", font=ctk.CTkFont(size=10, weight="bold"),
                             text_color=C['text'], anchor="w")
            v.pack(side="left", fill="x", expand=True)
            self.stat_lbls[key] = v
        ctk.CTkFrame(sf, fg_color='transparent').pack(fill="both", expand=True)

    # ────────────────────────────────────────────────────────────
    # EVENT HANDLERS
    # ────────────────────────────────────────────────────────────

    def _on_algo_change(self):
        if self.algo_var.get() == 'astar':
            self.h_label_w.pack(side="left", padx=(0, 4))
            self.h_menu.pack(side="left")
        else:
            self.h_label_w.pack_forget()
            self.h_menu.pack_forget()

    def _on_heuristic_change(self, val):
        for label, key in HEURISTIC_OPTIONS:
            if label == val:
                self.h_var.set(key)
                return

    def _on_speed(self, val):
        self.step_delay_ms = int(val)
        self.speed_lbl.configure(text=f"{self.step_delay_ms}ms")

    def _browse_file(self):
        idir = os.path.join(SCRIPT_DIR, "Inputs")
        if not os.path.isdir(idir):
            idir = SCRIPT_DIR
        fp = filedialog.askopenfilename(
            title="Chọn file input Futoshiki", initialdir=idir,
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if not fp:
            return
        try:
            self.puzzle = parse_input(fp)
            fname = os.path.basename(fp)
            self.file_btn.configure(text=f"\U0001f4c4 {fname}")
            self.file_info.configure(
                text=f"Size: {self.puzzle.N}×{self.puzzle.N}  |  {fname}",
                text_color=C['text'])
            self.grid_init.set_puzzle(self.puzzle)
            self.grid_sol.set_puzzle(self.puzzle)
            self._clear_log()
            self._reset_stats()
            self._log(f"\U0001f4c2 Loaded: {fname} ({self.puzzle.N}×{self.puzzle.N})")
        except Exception as e:
            self.file_info.configure(text=f"Lỗi: {e}", text_color=C['error'])

    def _start_solving(self):
        if not self.puzzle:
            self._log("\u26a0 Chưa chọn file input!", C['warning'])
            return
        if self.solving:
            return

        self.solving = True
        self.stop_event.clear()
        self.pause_event.set()
        self.step_count = 0
        self.step_queue = queue.Queue()
        self._pending_steps = deque()

        self._clear_log()
        self._reset_stats()
        self.grid_sol.clear_solution()
        self.solve_btn.configure(state="disabled")
        self.pause_btn.configure(state="normal", text="\u23f8 TẠM DỪNG", text_color='#1a1b26')
        self.stop_btn.configure(state="normal")
        self.stat_lbls['status'].configure(text="Đang giải...", text_color=C['warning'])

        algo = self.algo_var.get()
        # Map heuristic display label to key
        h_key = 'h2'
        if algo == 'astar':
            h_label = self.h_var.get()
            for label, key in HEURISTIC_OPTIONS:
                if label == h_label:
                    h_key = key
                    break
            # fallback: if h_var already has a key like 'h1'
            if h_key == 'h2' and h_label in ('h1', 'h2', 'h3'):
                h_key = h_label

        # Find display name for the algorithm
        algo_label = algo
        for lbl, k in ALGO_OPTIONS:
            if k == algo:
                algo_label = lbl
                break
        self._log(f"\u25b6 Bắt đầu: {algo_label}")
        if algo == 'astar':
            self._log(f"  Heuristic: {h_key.upper()}")

        self.solver_thread = threading.Thread(
            target=self._solver_run, args=(self.puzzle, algo, h_key), daemon=True)
        self.solver_thread.start()
        self._pending_steps = deque()
        self._poll()

    def _toggle_pause(self):
        if self.pause_event.is_set():
            # Hiện đang chạy -> Tạm dừng
            self.pause_event.clear()
            self.pause_btn.configure(text="\u25b6 TIẾP TỤC", text_color=C['text'])
            self._log("\u23f8 Đã tạm dừng. Bấm Tiếp tục để chạy tiếp.", C['warning'])
            self.stat_lbls['status'].configure(text="\u23f8 Tạm dừng", text_color=C['warning'])
        else:
            # Hiện đang dừng -> Tiếp tục
            self.pause_event.set()
            self.pause_btn.configure(text="\u23f8 TẠM DỪNG", text_color='#1a1b26')
            self._log("\u25b6 Đang tiếp tục...", C['success'])
            self.stat_lbls['status'].configure(text="Đang giải...", text_color=C['warning'])

    def _stop_solving(self):
        self.stop_event.set()
        self.pause_event.set()  # Phải báo unpause để thread có thể chạy nốt lệnh throw exception
        
        # Xoá toàn bộ các bước đang chờ hiển thị để GUI lập tức dừng lại
        self._pending_steps.clear()
        with self.step_queue.mutex:
            self.step_queue.queue.clear()
            
        self._log("\u23f9 Đang dừng...", C['warning'])

    # ────────────────────────────────────────────────────────────
    # SOLVER THREAD
    # ────────────────────────────────────────────────────────────

    def _solver_run(self, puzzle, algo, heuristic):
        import tracemalloc as tm

        # Smart throttle: skip GUI updates for fast solvers on big puzzles
        # Only send every Nth step to keep GUI responsive
        N = puzzle.N
        throttle = max(1, (N * N) // 4)  # e.g. N=4->4, N=9->20
        step_counter = [0]  # mutable for closure
        last_info = [None]  # keep last skipped step

        def cb(info):
            self.pause_event.wait()
            step_counter[0] += 1
            # Always send: result-like, info, done types
            if info.get('type') in ('info', 'done', 'result'):
                # Flush any skipped step first
                if last_info[0] is not None:
                    self.step_queue.put(last_info[0])
                    last_info[0] = None
                self.step_queue.put(info)
            elif step_counter[0] % throttle == 0:
                self.step_queue.put(info)
                last_info[0] = None
                time.sleep(0)
            else:
                last_info[0] = info  # store for potential flush

            if self.stop_event.is_set():
                raise StopSolverException()

        tm.start()
        t0 = time.time()
        try:
            solution, stats = run_solver(puzzle, algo, heuristic, step_callback=cb)
            elapsed = time.time() - t0
            _, peak = tm.get_traced_memory()
            tm.stop()
            if not isinstance(stats, dict):
                stats = {}
            if 'time' not in stats:
                stats['time'] = round(elapsed, 4)
            stats['memory_kb'] = round(peak / 1024, 2)
            # Flush last skipped step
            if last_info[0] is not None:
                self.step_queue.put(last_info[0])
            self.step_queue.put({'type': 'result', 'solution': solution, 'stats': stats})
        except StopSolverException:
            try: tm.stop()
            except: pass
            self.step_queue.put({'type': 'stopped'})
        except Exception as e:
            try: tm.stop()
            except: pass
            self.step_queue.put({'type': 'error', 'message': str(e),
                                 'tb': traceback.format_exc()})

    # ────────────────────────────────────────────────────────────
    # QUEUE POLLING & STEP PROCESSING
    # ────────────────────────────────────────────────────────────

    def _poll(self):
        try:
            count = 0
            while count < 1000:
                step = self.step_queue.get_nowait()
                self._pending_steps.append(step)
                count += 1
        except queue.Empty:
            pass

        if not self._pending_steps:
            if self.solving:
                self.after(15, self._poll)
            return

        # Handle batch rendering for high speeds
        batch_size = 1
        if self.step_delay_ms == 0:
            batch_size = 100
        elif self.step_delay_ms <= 5:
            batch_size = 20
        elif self.step_delay_ms <= 10:
            batch_size = 5

        processed = 0
        draw_assign = None
        draw_cell = None
        draw_hi = None
        need_draw = False
        log_buffer = []

        while self._pending_steps and processed < batch_size:
            step = self._pending_steps.popleft()
            t = step.get('type', '')
            
            # Done / Stopped / Error immediately abort the batch
            if t in ('result', 'stopped', 'error'):
                if log_buffer:
                    self._log("\n".join(log_buffer))
                if need_draw and self.use_delay.get():
                    self.grid_sol.update_state(draw_assign, hi_cell=draw_cell, hi_color=draw_hi)
                if t == 'result': self._on_done(step)
                elif t == 'stopped': self._on_stopped()
                elif t == 'error': self._on_error(step)
                return

            self.step_count += 1
            msg = step.get('message', '')
            icons = {'assign': '\U0001f7e2', 'backtrack': '\U0001f534',
                     'infer': '\U0001f535', 'prune': '\U0001f7e1',
                     'expand': '\U0001f537', 'info': '\u2139\ufe0f', 'done': '\u2705'}
            icon = icons.get(t, '\u2022')
            log_buffer.append(f"  {icon} Step {self.step_count}: {msg}")

            if t in ('backtrack',): draw_hi = 'backtrack'
            elif t in ('assign', 'infer'): draw_hi = 'assign'
            else: draw_hi = None

            draw_assign = step.get('assignment', {})
            draw_cell = step.get('cell')
            need_draw = True
            processed += 1

        if log_buffer:
            self._log("\n".join(log_buffer))
            
        if need_draw and self.use_delay.get():
            self.grid_sol.update_state(draw_assign, hi_cell=draw_cell, hi_color=draw_hi)

        if self.solving and self.use_delay.get() and self._pending_steps:
            delay = max(1, self.step_delay_ms)
            self.after(delay, self._poll)
            return

        if self.solving:
            self.after(15, self._poll)

    def _on_done(self, s):
        self.solving = False
        sol = s.get('solution')
        stats = s.get('stats', {})
        if sol:
            self._log(f"\n\u2705 Giải thành công! ({self.step_count} bước)", C['success'])
            self.grid_sol.update_state(sol)
            self.stat_lbls['status'].configure(text="\u2705 Thành công", text_color=C['success'])
        else:
            self._log(f"\n\u274c Không tìm thấy lời giải!", C['error'])
            self.stat_lbls['status'].configure(text="\u274c Không có lời giải", text_color=C['error'])
        self._update_stats(stats)
        self.solve_btn.configure(state="normal")
        self.pause_btn.configure(state="disabled", text="\u23f8 TẠM DỪNG")
        self.stop_btn.configure(state="disabled")

    def _on_stopped(self):
        self.solving = False
        self._log("\n\u23f9 Đã dừng.", C['warning'])
        self.stat_lbls['status'].configure(text="\u23f9 Đã dừng", text_color=C['warning'])
        self.solve_btn.configure(state="normal")
        self.pause_btn.configure(state="disabled", text="\u23f8 TẠM DỪNG")
        self.stop_btn.configure(state="disabled")

    def _on_error(self, s):
        self.solving = False
        self._log(f"\n\u274c Lỗi: {s.get('message','?')}", C['error'])
        tb = s.get('tb', '')
        if tb:
            self._log(tb, C['text_dim'])
        self.stat_lbls['status'].configure(text="\u274c Lỗi", text_color=C['error'])
        self.solve_btn.configure(state="normal")
        self.pause_btn.configure(state="disabled", text="\u23f8 TẠM DỪNG")
        self.stop_btn.configure(state="disabled")

    # ────────────────────────────────────────────────────────────
    # HELPERS
    # ────────────────────────────────────────────────────────────

    def _log(self, txt, color=None):
        self.log.configure(state="normal")
        self.log.insert("end", txt + "\n")
        if self.step_delay_ms > 2 or "\u2705" in txt or "\u274c" in txt:
            self.log.see("end")        
        self.log.configure(state="disabled")

    def _clear_log(self):
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")

    def _reset_stats(self):
        for v in self.stat_lbls.values():
            v.configure(text="—", text_color=C['text'])

    def _update_stats(self, stats):
        if not isinstance(stats, dict):
            return
        fmt = {
            'time':       ('time',       lambda v: f"{v:.4f}s"),
            'nodes':      ('nodes',      str),
            'backtracks': ('backtracks', str),
            'inferences': ('inferences', str),
            'iterations': ('iterations', str),
            'memory_kb':  ('memory',     lambda v: f"{v:.1f} KB"),
            'heuristic':  ('heuristic',  lambda v: str(v).upper()),
            'cnf_vars':   ('cnf_vars',   str),
            'cnf_clauses':('cnf_clauses',str),
        }
        for sk, (lk, fn) in fmt.items():
            if sk in stats and lk in self.stat_lbls:
                val = stats[sk]
                if val is not None and val != -1:
                    self.stat_lbls[lk].configure(text=fn(val))


# ================================================================
# ENTRY
# ================================================================

if __name__ == '__main__':
    app = FutoshikiApp()
    app.mainloop()
