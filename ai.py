import random

DIFFICULTY_EASY   = "easy"
DIFFICULTY_MEDIUM = "medium"
DIFFICULTY_HARD   = "hard"

class AIPlayer:
    def __init__(self, difficulty=DIFFICULTY_MEDIUM):
        self.difficulty = difficulty
        # memory[tile_index] = color
        self.memory = {}

    def observe(self, tile_index: int, color):
        """Record a tile the AI has seen."""
        # Easy AI might fail to observe
        if self.difficulty == DIFFICULTY_EASY:
            if random.random() < 0.3: # 30% chance to miss
                return
        self.memory[tile_index] = color

    def forget_tile(self, tile_index: int):
        self.memory.pop(tile_index, None)

    def choose_moves(self, available_indices: list) -> tuple:
        """
        Choose 2 tile indices to flip based on difficulty.
        """
        available_set = set(available_indices)
        known_available = {idx: col for idx, col in self.memory.items()
                           if idx in available_set}

        # 1. Look for known matching pairs
        color_to_indices = {}
        for idx, col in known_available.items():
            color_to_indices.setdefault(col, []).append(idx)

        matches = [indices[:2] for col, indices in color_to_indices.items() if len(indices) >= 2]

        # Difficulty Logic
        if self.difficulty == DIFFICULTY_EASY:
            # 50% chance to ignore known matches and play randomly
            if matches and random.random() > 0.5:
                pair = matches[0]
                return (pair[0], pair[1])
        elif self.difficulty == DIFFICULTY_MEDIUM:
            # 85% chance to take the match if known
            if matches and random.random() < 0.85:
                pair = matches[0]
                return (pair[0], pair[1])
        else: # HARD
            if matches:
                pair = matches[0]
                return (pair[0], pair[1])

        # 2. Pick one known + one random unseen (or both random)
        unseen = [i for i in available_indices if i not in self.memory]
        
        if self.difficulty == DIFFICULTY_HARD:
            # Hard AI prioritizes picking a tile it knows to see if it can find its match
            if known_available and unseen:
                return (list(known_available.keys())[0], random.choice(unseen))
        
        # Default: pick 2 random (preferring unseen if possible)
        if len(unseen) >= 2:
            chosen = random.sample(unseen, 2)
            return (chosen[0], chosen[1])
        
        # Final fallback
        chosen = random.sample(available_indices, 2)
        return (chosen[0], chosen[1])

    def reset(self):
        self.memory = {}
