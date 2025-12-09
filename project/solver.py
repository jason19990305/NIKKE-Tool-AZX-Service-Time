# solver.py
from itertools import combinations

class Solver:
    def __init__(self, target_sum=10):
        self.target = target_sum

    def _build_prefix_sum_and_nodes(self, matrix):
        rows = len(matrix)
        cols = len(matrix[0]) if rows > 0 else 0
        p_sum = [[0] * (cols + 1) for _ in range(rows + 1)]
        nodes = []
        
        for r in range(rows):
            for c in range(cols):
                val = matrix[r][c]
                p_sum[r+1][c+1] = (p_sum[r][c+1] + p_sum[r+1][c] - p_sum[r][c] + val)
                if val > 0:
                    nodes.append((r, c))
        return rows, cols, p_sum, nodes

    def solve(self, matrix):
        """
        [Backward Compatibility] Return only "one" best solution (smallest area first)
        """
        moves = self.find_all_moves(matrix, sort_by_area=True)
        return moves[0] if moves else None

    def find_all_moves(self, matrix, sort_by_area=True):
        """
        [New Feature] Return "all" possible solutions for the current board
        Return format: list of (r1, c1, r2, c2)
        """
        rows, cols, p_sum, nodes = self._build_prefix_sum_and_nodes(matrix)
        valid_moves = []

        # 1. Check single point (1x1)
        for r, c in nodes:
            if matrix[r][c] == self.target:
                valid_moves.append((r, c, r, c))

        # 2. Check diagonals (rectangle)
        candidates = []
        for p1, p2 in combinations(nodes, 2):
            r1, c1 = p1
            r2, c2 = p2
            
            min_r, max_r = min(r1, r2), max(r1, r2)
            min_c, max_c = min(c1, c2), max(c1, c2)
            
            # Use prefix sum to get total in O(1)
            rect_sum = (p_sum[max_r+1][max_c+1] - 
                        p_sum[min_r][max_c+1] - 
                        p_sum[max_r+1][min_c] + 
                        p_sum[min_r][min_c])
            
            if rect_sum == self.target:
                area = (max_r - min_r + 1) * (max_c - min_c + 1)
                # Store in tuple: (area, move_tuple)
                candidates.append((area, (r1, c1, r2, c2)))

        # 3. Sort
        if sort_by_area:
            # Sort by smallest area first (usually less likely to block other solutions)
            candidates.sort(key=lambda x: x[0])
        
        # Extract move part
        valid_moves.extend([c[1] for c in candidates])
        
        return valid_moves

if __name__ == "__main__":
    solver = Solver(10)
    test_grid = [
        [0, 0, 0, 6, 0],
        [4, 0, 0, 0, 0],
        [0, 5, 0, 5, 0]
    ]
    all_moves = solver.find_all_moves(test_grid)
    print(f"找到 {len(all_moves)} 組解:")
    for m in all_moves:
        print(m)