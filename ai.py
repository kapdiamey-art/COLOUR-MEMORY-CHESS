"""
ai.py - AI Memory Logic for Color Memory Chess
The AI stores memory of revealed tiles and plays smartly.
"""

import random


class AIPlayer:
    def __init__(self):
        # memory[tile_index] = color (once AI has seen it)
        self.memory = {}

    def observe(self, tile_index: int, color):
        """Record a tile the AI has seen."""
        self.memory[tile_index] = color

    def forget_tile(self, tile_index: int):
        """Optionally remove a tile from memory (e.g. after it's matched)."""
        self.memory.pop(tile_index, None)

    def choose_moves(self, available_indices: list) -> tuple:
        """
        Choose 2 tile indices to flip.
        Strategy:
          1. If AI knows a matching pair in available tiles → pick it.
          2. If AI knows one tile of a pair → pick that + a random unseen tile.
          3. Otherwise → pick 2 random unseen tiles (prefer unseen over seen).
        Returns (first_index, second_index)
        """
        available_set = set(available_indices)

        # Build known tiles that are still available
        known_available = {idx: col for idx, col in self.memory.items()
                           if idx in available_set}

        # 1. Check for a known matching pair
        color_to_indices = {}
        for idx, col in known_available.items():
            color_to_indices.setdefault(col, []).append(idx)

        for col, indices in color_to_indices.items():
            if len(indices) >= 2:
                # Found a guaranteed match
                chosen = indices[:2]
                return (chosen[0], chosen[1])

        # 2. Know at least one tile — pick it + random unseen
        unseen = [i for i in available_indices if i not in self.memory]

        if known_available and unseen:
            first = random.choice(list(known_available.keys()))
            second = random.choice(unseen)
            return (first, second)

        # 3. Both random (prefer unseen tiles)
        if len(unseen) >= 2:
            chosen = random.sample(unseen, 2)
            return (chosen[0], chosen[1])

        # Fallback — just pick any 2 available
        chosen = random.sample(list(available_indices), 2)
        return (chosen[0], chosen[1])

    def reset(self):
        """Reset memory for a new game."""
        self.memory = {}
