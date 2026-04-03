import copy


class KnowledgeBase:
    """Knowledge Base luu tru facts va domains."""
    
    def __init__(self, puzzle, initial_assignment):
        self.puzzle = puzzle
        self.N = puzzle.N
        self.facts = copy.copy(initial_assignment)
        self.inferences_count = 0
        
        # Khoi tao domains cho cac o trong
        self.domains = {}
        for r in range(self.N):
            for c in range(self.N):
                if (r, c) not in self.facts:
                    self.domains[(r, c)] = set(range(1, self.N + 1))
        
        self._update_domains_from_facts()
    
    def add_fact(self, r, c, value):
        """Them mot fact moi vao KB."""
        if (r, c) in self.facts:
            return False
        
        self.facts[(r, c)] = value
        self.inferences_count += 1
        
        if (r, c) in self.domains:
            del self.domains[(r, c)]
        
        self._update_domains_after_assignment(r, c, value)
        return True
    
    def _update_domains_from_facts(self):
        for (r, c), value in self.facts.items():
            self._update_domains_after_assignment(r, c, value)
    
    def _update_domains_after_assignment(self, r, c, value):
        """Update domains sau khi gan o (r,c) = value."""
        # Loai bo value khoi cac o cung hang
        for col in range(self.N):
            if (r, col) in self.domains:
                self.domains[(r, col)].discard(value)
        
        # Loai bo value khoi cac o cung cot
        for row in range(self.N):
            if (row, c) in self.domains:
                self.domains[(row, c)].discard(value)
        
        self._apply_inequality_constraints_for_cell(r, c, value)
    
    def _apply_inequality_constraints_for_cell(self, r, c, value):
        """Ap dung rang buoc bat dang thuc tu o (r,c)."""
        # Horizontal constraint voi o ben phai
        if c < self.N - 1 and (r, c + 1) in self.domains:
            if self.puzzle.h_con[r][c] == 1:
                self.domains[(r, c + 1)] = {v for v in self.domains[(r, c + 1)] if v > value}
            elif self.puzzle.h_con[r][c] == -1:
                self.domains[(r, c + 1)] = {v for v in self.domains[(r, c + 1)] if v < value}
        
        # Horizontal constraint voi o ben trai
        if c > 0 and (r, c - 1) in self.domains:
            if self.puzzle.h_con[r][c - 1] == 1:
                self.domains[(r, c - 1)] = {v for v in self.domains[(r, c - 1)] if v < value}
            elif self.puzzle.h_con[r][c - 1] == -1:
                self.domains[(r, c - 1)] = {v for v in self.domains[(r, c - 1)] if v > value}
        
        # Vertical constraint voi o phia duoi
        if r < self.N - 1 and (r + 1, c) in self.domains:
            if self.puzzle.v_con[r][c] == 1:
                self.domains[(r + 1, c)] = {v for v in self.domains[(r + 1, c)] if v > value}
            elif self.puzzle.v_con[r][c] == -1:
                self.domains[(r + 1, c)] = {v for v in self.domains[(r + 1, c)] if v < value}
        
        # Vertical constraint voi o phia tren
        if r > 0 and (r - 1, c) in self.domains:
            if self.puzzle.v_con[r - 1][c] == 1:
                self.domains[(r - 1, c)] = {v for v in self.domains[(r - 1, c)] if v < value}
            elif self.puzzle.v_con[r - 1][c] == -1:
                self.domains[(r - 1, c)] = {v for v in self.domains[(r - 1, c)] if v > value}
    
    def is_complete(self):
        return len(self.facts) == self.N * self.N
    
    def is_consistent(self):
        for domain in self.domains.values():
            if len(domain) == 0:
                return False
        return True
    
    def get_inferred_count(self):
        return self.inferences_count


def apply_singleton_domain_rule(kb):
    """Neu mot o chi co 1 gia tri kha thi, gan ngay."""
    count = 0
    
    while True:
        singleton_found = False
        
        for (r, c), domain in list(kb.domains.items()):
            if len(domain) == 1:
                value = list(domain)[0]
                if kb.add_fact(r, c, value):
                    count += 1
                    singleton_found = True
                    break
        
        if not singleton_found:
            break
        
        if not kb.is_consistent():
            break
    
    return count


def apply_row_uniqueness_rule(kb):
    """Neu mot hang co N-1 o da dien, suy ra o cuoi."""
    count = 0
    N = kb.N
    
    for r in range(N):
        filled_cells = [(r, c) for c in range(N) if (r, c) in kb.facts]
        
        if len(filled_cells) == N - 1:
            empty_cell = None
            for c in range(N):
                if (r, c) not in kb.facts:
                    empty_cell = (r, c)
                    break
            
            if empty_cell and empty_cell in kb.domains:
                used_values = {kb.facts[(r, c)] for c in range(N) if (r, c) in kb.facts}
                all_values = set(range(1, N + 1))
                missing_values = all_values - used_values
                
                if len(missing_values) == 1:
                    missing_value = missing_values.pop()
                    if kb.add_fact(empty_cell[0], empty_cell[1], missing_value):
                        count += 1
    
    return count


def apply_col_uniqueness_rule(kb):
    """Neu mot cot co N-1 o da dien, suy ra o cuoi."""
    count = 0
    N = kb.N
    
    for c in range(N):
        filled_cells = [(r, c) for r in range(N) if (r, c) in kb.facts]
        
        if len(filled_cells) == N - 1:
            empty_cell = None
            for r in range(N):
                if (r, c) not in kb.facts:
                    empty_cell = (r, c)
                    break
            
            if empty_cell and empty_cell in kb.domains:
                used_values = {kb.facts[(r, c)] for r in range(N) if (r, c) in kb.facts}
                all_values = set(range(1, N + 1))
                missing_values = all_values - used_values
                
                if len(missing_values) == 1:
                    missing_value = missing_values.pop()
                    if kb.add_fact(empty_cell[0], empty_cell[1], missing_value):
                        count += 1
    
    return count


def apply_hidden_single_rule(kb):
    """Neu chi co mot o co the chua gia tri v, gan v cho o do."""
    count = 0
    N = kb.N
    
    # Check rows
    for row_idx in range(N):
        for value in range(1, N + 1):
            if any((row_idx, col) in kb.facts and kb.facts[(row_idx, col)] == value 
                   for col in range(N)):
                continue
            
            possible_cells = [(row_idx, col) for col in range(N) 
                            if (row_idx, col) in kb.domains and value in kb.domains[(row_idx, col)]]
            
            if len(possible_cells) == 1:
                cell = possible_cells[0]
                if kb.add_fact(cell[0], cell[1], value):
                    count += 1
                    return count
    
    # Check columns
    for col_idx in range(N):
        for value in range(1, N + 1):
            if any((row, col_idx) in kb.facts and kb.facts[(row, col_idx)] == value 
                   for row in range(N)):
                continue
            
            possible_cells = [(row, col_idx) for row in range(N) 
                            if (row, col_idx) in kb.domains and value in kb.domains[(row, col_idx)]]
            
            if len(possible_cells) == 1:
                cell = possible_cells[0]
                if kb.add_fact(cell[0], cell[1], value):
                    count += 1
                    return count
    
    return count


def solve_forward_chaining(puzzle):
    """Giai Futoshiki puzzle bang Forward Chaining."""
    from futoshiki import build_initial_assignment
    
    initial_assignment = build_initial_assignment(puzzle)
    kb = KnowledgeBase(puzzle, initial_assignment)
    
    iterations = 0
    max_iterations = 100
    
    # Main inference loop
    while not kb.is_complete() and iterations < max_iterations:
        iterations += 1
        new_facts_count = 0
        
        new_facts_count += apply_singleton_domain_rule(kb)
        new_facts_count += apply_row_uniqueness_rule(kb)
        new_facts_count += apply_col_uniqueness_rule(kb)
        new_facts_count += apply_hidden_single_rule(kb)
        
        if new_facts_count == 0:
            break
        
        if not kb.is_consistent():
            return None, {
                'iterations': iterations,
                'inferences': kb.get_inferred_count(),
                'nodes': iterations
            }
    
    if kb.is_complete():
        if puzzle.is_valid(kb.facts):
            return kb.facts, {
                'iterations': iterations,
                'inferences': kb.get_inferred_count(),
                'nodes': iterations
            }
        else:
            return None, {
                'iterations': iterations,
                'inferences': kb.get_inferred_count(),
                'nodes': iterations
            }
    else:
        return None, {
            'iterations': iterations,
            'inferences': kb.get_inferred_count(),
            'nodes': iterations,
            'incomplete': True
        }
