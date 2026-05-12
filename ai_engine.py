import math
import random

class AIEngine:
    def __init__(self, difficulty="MEDIUM"):
        self.difficulty = difficulty # "EASY", "MEDIUM", "HARD"

    def get_best_move(self, state):
        # AI Logic: First check if we have a guaranteed match in memory
        memory_pairs = self._get_memory_matches(state)
        
        # Difficulty-based memory filtering
        if self.difficulty == "EASY":
            if random.random() > 0.3: memory_pairs = [] # 70% chance to "forget"
            depth = 1
        elif self.difficulty == "MEDIUM":
            if random.random() > 0.7: memory_pairs = [] # 30% chance to "forget"
            depth = 2
        else: # HARD
            depth = 3 # 100% memory
            
        if memory_pairs:
            # We found a match! Use Alpha-Beta to confirm it's the best move
            _, move = self.alpha_beta(state, depth, -math.inf, math.inf, True)
            return move if move else memory_pairs[0]
            
        # No guaranteed matches? Use EXPECTIMAX to play probabilistically
        _, move = self.expectimax(state, depth, True)
        return move

    def _get_memory_matches(self, state):
        known = {}
        for idx, color in state.memory.items():
            if not state.tiles[idx]['is_matched']:
                known[color] = known.get(color, []) + [idx]
        
        for color, indices in known.items():
            if len(indices) >= 2:
                return (indices[0], indices[1])
        return None

    def alpha_beta(self, state, depth, alpha, beta, is_maximizing):
        if depth == 0 or state.is_terminal():
            return state.evaluate(), None

        moves = state.get_possible_moves()
        if not moves: return state.evaluate(), None
        
        best_move = random.choice(moves)
        if is_maximizing:
            best_score = -math.inf
            for move in moves:
                score, _ = self.alpha_beta(state.simulate_move(move), depth - 1, alpha, beta, False)
                if score > best_score:
                    best_score = score
                    best_move = move
                alpha = max(alpha, best_score)
                if beta <= alpha: break
            return best_score, best_move
        else:
            best_score = math.inf
            for move in moves:
                score, _ = self.alpha_beta(state.simulate_move(move), depth - 1, alpha, beta, True)
                if score < best_score:
                    best_score = score
                    best_move = move
                beta = min(beta, best_score)
                if beta <= alpha: break
            return best_score, best_move

    def expectimax(self, state, depth, is_maximizing):
        if depth == 0 or state.is_terminal():
            return state.evaluate(), None

        moves = state.get_possible_moves()
        if not moves: return state.evaluate(), None
        
        best_move = random.choice(moves)
        if is_maximizing:
            best_score = -math.inf
            for move in moves:
                score, _ = self.expectimax(state.simulate_move(move), depth - 1, False)
                if score > best_score:
                    best_score = score
                    best_move = move
            return best_score, best_move
        else:
            # Chance node: Average scores of all moves
            total_score = 0
            for move in moves:
                score, _ = self.expectimax(state.simulate_move(move), depth - 1, True)
                total_score += score
            return total_score / len(moves), None
