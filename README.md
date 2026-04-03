# Futoshiki Solver - FOL Inference Algorithms

Giai Futoshiki puzzle su dung cac thuat toan suy dien First-Order Logic (FOL).

**Do an mon:** CSC14003 - Artificial Intelligence  
**Hoc ky:** 2025-2026

---

## Algorithms

- **Forward Chaining (FC)** - Suy dien huong du lieu
- **Backtracking (BT)** - Tim kiem voi quay lui

---

## Cai dat

```bash
cd Source
pip install -r requirements.txt
```

---

## Cach chay

```bash
python main.py <input_file> <algorithm> [output_file]
```

**Vi du:**

```bash
# Forward Chaining
python main.py Inputs/input-01.txt fc

# Backtracking
python main.py Inputs/input-02.txt bt Outputs/output-02.txt
```

---

## Thuat toan

### Forward Chaining
- Suy dien huong du lieu (data-driven inference)
- Su dung 4 quy tac suy dien:
  - Row/Column Uniqueness
  - Domain Elimination
  - Inequality Constraints
  - Hidden Single Rule

### Backtracking
- Tim kiem CSP voi quay lui
- Cac toi uu hoa:
  - MRV (Minimum Remaining Values) heuristic
  - Forward Checking
  - Domain management

---

## Input Format

```
N                              # Kich thuoc grid (NxN)
v1,v2,...,vN                   # Hang 1 (0 = o trong)
v1,v2,...,vN                   # Hang 2
...
c1,c2,...,cN-1                 # Rang buoc ngang hang 1 (0=none, 1='<', -1='>')
c1,c2,...,cN-1                 # Rang buoc ngang hang 2
...
c1,c2,...,cN                   # Rang buoc doc cot 1
c1,c2,...,cN                   # Rang buoc doc cot 2
...
```

---

## Output Format

```
N
v1,v2,...,vN                   # Loi giai hang 1
v1,v2,...,vN                   # Loi giai hang 2
...
```

---

## Project Structure

```
Futoshiki-FOL-Inference-Algorithms/
├── Source/
│   ├── main.py                # Entry point
│   ├── futoshiki.py           # Core puzzle logic
│   ├── forward_chain.py       # Forward Chaining algorithm
│   ├── backtracking.py        # Backtracking algorithm
│   ├── display.py             # Output formatting
│   ├── Inputs/                # Test inputs
│   └── Outputs/               # Solutions
└── README.md
```

---

## Performance

| Puzzle Size | FC Time | BT Time | Complete? |
|-------------|---------|---------|-----------|
| 4x4 (easy)  | <0.1s   | <0.1s   | Yes       |
| 4x4 (hard)  | <0.1s   | <1s     | BT only   |
| 5x5         | <0.5s   | <5s     | BT only   |

**Luu y:** Forward Chaining co the khong giai duoc tat ca puzzle (incomplete algorithm).

---

## License

MIT License - CSC14003 Academic Project
