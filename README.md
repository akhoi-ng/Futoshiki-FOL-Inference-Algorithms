# Futoshiki Solver — FOL Inference Algorithms

Giải Futoshiki puzzle sử dụng các thuật toán suy diễn First-Order Logic (FOL).

**Môn học:** CSC14003 - Cơ sở Trí tuệ Nhân tạo  
**Học kỳ:** 2025-2026

---

## Thuật toán

| Ký hiệu | Tên đầy đủ | Mô tả |
|---------|------------|-------|
| `fc` | Forward Chaining | Suy diễn hướng dữ liệu (data-driven) |
| `bt` | Backtracking | Tìm kiếm CSP với quay lui + MRV |
| `bc` | Backward Chaining | Suy diễn hướng mục tiêu (goal-driven, Prolog-style) |
| `astar` | A\* Search | Tìm kiếm heuristic A\* với 3 hàm đánh giá |
| `cnf` | CNF Generator | Sinh mệnh đề CNF từ ràng buộc FOL |

---

## Cài đặt

```bash
cd Source
pip install -r requirements.txt
```

---

## Cách chạy

### 1. Command-line (CLI)

```bash
python main.py <input_file> <algorithm> [output_file] [heuristic]
```

**Cú pháp đầy đủ:**

| Tham số | Bắt buộc | Mô tả |
|---------|----------|-------|
| `input_file` | ✅ | Đường dẫn đến file input (`.txt`) |
| `algorithm` | ✅ | Một trong: `fc`, `bt`, `bc`, `astar`, `cnf` |
| `output_file` | ❌ | Đường dẫn lưu kết quả (tùy chọn) |
| `heuristic` | ❌ | Chỉ dùng với `astar`: `h1`, `h2` (mặc định), `h3` |

**Ví dụ:**

```bash
# Forward Chaining
python main.py Inputs/input-01.txt fc

# Backtracking (kèm lưu file output)
python main.py Inputs/input-02.txt bt Outputs/output-02.txt

# Backward Chaining
python main.py Inputs/input-03.txt bc

# A* Search — dùng heuristic h2 (mặc định)
python main.py Inputs/input-01.txt astar Outputs/output-01.txt

# A* Search — dùng heuristic h1 (Trivial)
python main.py Inputs/input-01.txt astar Outputs/output-01.txt h1

# A* Search — dùng heuristic h3 (AC-3)
python main.py Inputs/input-01.txt astar Outputs/output-01.txt h3

# CNF Generator
python main.py Inputs/input-01.txt cnf
```

> **Lưu ý:** Nếu chạy `python main.py` không có tham số, chương trình sẽ tự động khởi động **GUI**.

---

### 2. Giao diện đồ họa (GUI)

```bash
cd Source
python main.py
```

Giao diện sẽ mở ở chế độ toàn màn hình với theme tối (Tokyo Night).

**Hướng dẫn sử dụng GUI:**

1. **Chọn file input** — Click **"Chọn file input..."** để mở file `.txt` trong thư mục `Inputs/`.
2. **Chọn thuật toán** — Chọn một trong 5 radio button: Forward Chaining, Backtracking, Backward Chaining, A\* Search, CNF Generator.
3. **Chọn Heuristic (chỉ với A\*)** — Khi chọn **A\* Search**, một dropdown **Heuristic** sẽ xuất hiện với 3 tùy chọn:
   - `H1 - Trivial`: Đếm số ô chưa gán (nhanh, kém chính xác).
   - `H2 - Domain Wipeout`: Phát hiện dead-end sớm, **mặc định**.
   - `H3 - AC-3`: Lan truyền ràng buộc đầy đủ (chậm hơn, thông minh hơn).
4. **Điều chỉnh tốc độ** — Dùng thanh trượt **Tốc độ** (0–500ms mỗi bước). Bật/tắt **"Hiển thị từng bước"** để xem animation trực quan.
5. **Bắt đầu giải** — Click **▶ GIẢI**.
6. **Kiểm soát quá trình:**
   - **⏸ TẠM DỪNG** — Tạm dừng, click lại để tiếp tục.
   - **⏹ DỪNG HẲN** — Dừng và huỷ quá trình giải.
7. **Xem kết quả** — Bảng bên phải hiển thị trạng thái ban đầu và quá trình/kết quả giải. Bảng **THỐNG KÊ** bên phải cập nhật thời gian, số nodes, số backtracks, bộ nhớ, v.v.

---

### 3. Benchmark (Đo hiệu suất)

Chạy toàn bộ thuật toán trên tất cả input và xuất kết quả ra CSV:

```bash
cd Source

# Chạy mặc định (tất cả thuật toán, tất cả input, timeout 600s)
python benchmark_engines.py

# Chỉ định thuật toán và timeout
python benchmark_engines.py --algorithms fc bt bc astar cnf --timeout 60

# Lưu kết quả ra file CSV
python benchmark_engines.py --csv Results/benchmark.csv

# Bật đo bộ nhớ (chậm hơn nhưng có cột mem_peak_kb)
python benchmark_engines.py --track-mem --csv Results/benchmark.csv

# Lọc input theo glob pattern
python benchmark_engines.py --inputs "Inputs/input-0[1-5].txt" --csv Results/small.csv

# Chạy đầy đủ: đo cả thời gian lẫn bộ nhớ, lưu CSV
python benchmark_engines.py --algorithms fc bt bc astar --timeout 120 --track-mem --csv Results/benchmark.csv
```

**Các tùy chọn benchmark:**

| Tùy chọn | Mặc định | Mô tả |
|----------|----------|-------|
| `--inputs` | `Inputs/input-*.txt` | Glob pattern chọn file input |
| `--algorithms` | `fc bt bc astar cnf` | Danh sách thuật toán cần chạy |
| `--timeout` | `600` | Timeout (giây) mỗi cặp (input, algo) |
| `--csv` | _(không lưu)_ | Đường dẫn file CSV output |
| `--track-mem` | _(tắt)_ | Bật đo bộ nhớ đỉnh (peak memory) |

> **Lưu ý:** Khi `astar` có trong `--algorithms`, benchmark tự động expand thành 3 biến thể: `astar-h1`, `astar-h2`, `astar-h3`.

---

### 4. Vẽ biểu đồ (Plot Charts)

Sau khi có file CSV từ benchmark, chạy script sau để sinh 3 biểu đồ so sánh:

```bash
cd Source

# Chạy mặc định (đọc Results/benchmark.csv, lưu vào Results/Charts/)
python plot_charts.py
```

Script tạo 3 file ảnh PNG trong thư mục `Results/Charts/`:

| File | Nội dung |
|------|----------|
| `chart_time.png` | Thời gian chạy (log scale) |
| `chart_memory.png` | Bộ nhớ đỉnh (KB) |
| `chart_nodes.png` | Số Nodes/Inferences đã mở rộng (log scale) |

> **Yêu cầu:** File `Results/benchmark.csv` phải tồn tại trước (chạy benchmark với `--csv` trước).

---

## Chi tiết thuật toán

### Forward Chaining (`fc`)
- Suy diễn hướng dữ liệu (data-driven inference).
- Áp dụng 4 quy tắc FOL lặp đi lặp lại cho đến khi đạt fixpoint:
  - **Row/Column Uniqueness** — Mỗi giá trị xuất hiện đúng một lần mỗi hàng/cột.
  - **Domain Elimination** — Loại các giá trị không hợp lệ khỏi domain.
  - **Inequality Constraints** — Áp dụng ràng buộc bất đẳng thức `<`, `>`.
  - **Hidden Single Rule** — Nếu chỉ còn một ô có thể chứa giá trị `v` trong hàng/cột thì gán.
- Nếu FC đạt fixpoint nhưng chưa hoàn tất, Backtracking sẽ hỗ trợ phần còn lại.

### Backtracking (`bt`)
- Tìm kiếm CSP với quay lui.
- Tối ưu hóa:
  - **MRV** (Minimum Remaining Values) — Chọn ô có ít giá trị hợp lệ nhất trước.
  - **Forward Checking** — Kiểm tra ràng buộc sớm sau mỗi lần gán.
  - **Domain management** — Quản lý domain động khi gán/huỷ gán.

### Backward Chaining (`bc`)
- Suy diễn hướng mục tiêu (goal-directed), kiểu Prolog.
- Bắt đầu từ mục tiêu, truy vết các tiên đề cần thiết để chứng minh.

### A\* Search (`astar`)
- Tìm kiếm heuristic với hàng đợi ưu tiên (min-heap).
- Dùng MRV để chọn ô mở rộng tốt nhất.
- Hỗ trợ **3 heuristic**:

| Heuristic | Tên | Mô tả |
|-----------|-----|-------|
| `h1` | Trivial | Đếm số ô chưa gán — `h = N²− |assignment|` |
| `h2` | Domain Wipeout | Phát hiện dead-end sớm qua forward checking; đếm ô trong chuỗi bất đẳng thức chưa hoàn thành. **Mặc định.** |
| `h3` | AC-3 | Lan truyền ràng buộc đầy đủ (Arc Consistency); tổng kích thước domain còn lại |

### CNF Generator (`cnf`)
- Sinh ra các mệnh đề CNF (Conjunctive Normal Form) từ ràng buộc FOL của puzzle.
- Phục vụ mục đích nghiên cứu và báo cáo.

---

## Định dạng Input

```
N                              # Kích thước grid (NxN)
v1,v2,...,vN                   # Hàng 1 (0 = ô trống)
v1,v2,...,vN                   # Hàng 2
...                            # Hàng N
c1,c2,...,cN-1                 # Ràng buộc ngang hàng 1 (0=none, 1='<', -1='>')
c1,c2,...,cN-1                 # Ràng buộc ngang hàng 2
...                            # Ràng buộc ngang hàng N
c1,c2,...,cN                   # Ràng buộc dọc cột 1
c1,c2,...,cN                   # Ràng buộc dọc cột 2
...                            # Ràng buộc dọc cột N
```

**Ví dụ input 4×4:**
```
4
0,2,0,0
0,0,3,0
4,0,0,1
0,0,2,0
1,0,-1
0,1,0
0,-1,0
1,0,0
0,0,1
0,1,0
0,0,-1
```

---

## Định dạng Output

```
N
v1,v2,...,vN                   # Lời giải hàng 1
v1,v2,...,vN                   # Lời giải hàng 2
...
```

---

## Cấu trúc dự án

```
Futoshiki-FOL-Inference-Algorithms/
├── Source/
│   ├── main.py                # Entry point (CLI + khởi động GUI)
│   ├── gui.py                 # Giao diện đồ họa (customtkinter)
│   ├── futoshiki.py           # Core: parse input, domain, constraints
│   ├── forward_chain.py       # Forward Chaining algorithm
│   ├── backtracking.py        # Backtracking algorithm
│   ├── backward_chain.py      # Backward Chaining (Prolog-style)
│   ├── astar.py               # A* Search (h1/h2/h3)
│   ├── cnf_generator.py       # CNF Generator
│   ├── display.py             # Output formatting
│   ├── benchmark_engines.py   # Benchmark runner (multi-process)
│   ├── plot_charts.py         # Vẽ biểu đồ từ kết quả benchmark
│   ├── Inputs/                # 12 file test (4×4 → 9×9)
│   ├── Outputs/               # Lời giải xuất ra
│   └── Results/               # File CSV và biểu đồ benchmark
│       └── Charts/            # Ảnh PNG biểu đồ
├── Docs/
│   └── Project_02_Futoshiki.md  # Đặc tả đề bài
├── requirements.txt
└── README.md
```

---

## Hiệu suất (tham khảo)

| Kích thước | FC | BT | BC | A\* (h2) | A\* (h3) |
|------------|----|----|-----|----------|----------|
| 4×4 (dễ) | <0.01s | <0.01s | <0.1s | <0.1s | <0.2s |
| 4×4 (khó) | <0.1s | <0.5s | ~1s | <1s | <2s |
| 5×5 | <0.5s | <5s | timeout | <10s | <30s |
| 6×6+ | BT-only | <60s | timeout | timeout | timeout |

> **Lưu ý:**
> - **Forward Chaining** là thuật toán không đầy đủ (incomplete): có thể không giải được mọi puzzle, sẽ gọi BT để giải phần còn lại.
> - **A\* với h1** thường nhanh hơn nhưng kém chính xác; **h3 (AC-3)** thông minh nhất nhưng tốn nhiều thời gian tính heuristic hơn.
> - Benchmark thực tế phụ thuộc vào cấu trúc cụ thể của từng puzzle.

---

## License

MIT License — CSC14003 Academic Project
