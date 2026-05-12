import copy

class GameState:
    def __init__(self, tiles_data, ai_memory, ai_score, player_score, player_turn=True):
        self.tiles = tiles_data # List of {index, color, is_matched, is_revealed}
        self.memory = ai_memory # {index: color}
        self.ai_score = ai_score
        self.player_score = player_score
        self.player_turn = player_turn
        
    def get_possible_moves(self):
        # AI moves optimization: Too many pairs (24 tiles = 276 pairs)
        # We only need to consider:
        # 1. Matches we know in memory
        # 2. A few unknown tiles to test
        
        available = [i for i, t in enumerate(self.tiles) if not t['is_matched']]
        if len(available) < 2: return []

        # 1. Check memory for matches
        known = {}
        for idx in available:
            if idx in self.memory:
                color = self.memory[idx]
                known[color] = known.get(color, []) + [idx]
        
        for color, indices in known.items():
            if len(indices) >= 2:
                # If we have a match, that's the only move we care about (dominant)
                return [(indices[0], indices[1])]
        
        # 2. No known matches? Limit the search to a few unknown tiles
        # Instead of 276 pairs, just try the first few available
        moves = []
        limit = 6 # Only consider first 6 available tiles (~15 pairs)
        subset = available[:limit]
        for i in range(len(subset)):
            for j in range(i + 1, len(subset)):
                moves.append((subset[i], subset[j]))
        return moves

    def is_terminal(self):
        return all(t['is_matched'] for t in self.tiles)

    def evaluate(self):
        # AI wants to maximize AI - Player
        base = self.ai_score - self.player_score
        
        # Bonus for known pairs in memory that aren't matched yet
        known_counts = {}
        for idx, color in self.memory.items():
            if not self.tiles[idx]['is_matched']:
                known_counts[color] = known_counts.get(color, []) + [idx]
        
        pairs_in_memory = 0
        for color, indices in known_counts.items():
            if len(indices) >= 2:
                pairs_in_memory += 1
                
        return base * 10 + pairs_in_memory * 5

    def simulate_move(self, move):
        idx1, idx2 = move
        new_state = copy.deepcopy(self)
        t1, t2 = new_state.tiles[idx1], new_state.tiles[idx2]
        
        # If both are in memory or we know they match
        if t1['color'] == t2['color']:
            t1['is_matched'] = True
            t2['is_matched'] = True
            if new_state.player_turn:
                new_state.player_score += 1
            else:
                new_state.ai_score += 1
        
        new_state.player_turn = not new_state.player_turn
        return new_state
