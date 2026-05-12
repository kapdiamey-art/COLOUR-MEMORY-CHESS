"""
game.py - Core Game Logic and Turn System for Color Memory Chess
"""

import random
import math
from ai import AIPlayer

# === TILE COLORS (12 pairs = 24 tiles) ===
TILE_COLORS = [
    (255,  80,  80),   # red
    ( 80, 200, 120),   # green
    ( 80, 160, 255),   # blue
    (255, 200,  60),   # yellow
    (200,  80, 255),   # purple
    ( 80, 230, 230),   # cyan
    (255, 140,  40),   # orange
    (255, 100, 180),   # pink
    (140, 255, 100),   # lime
    (100, 100, 255),   # indigo
    (255, 255, 255),   # white
    (150, 150, 150),   # grey
]

STATE_PLAYER_TURN  = "player"
STATE_AI_TURN      = "ai"
STATE_FLIP_BACK    = "flip_back"
STATE_AI_THINKING  = "ai_thinking"
STATE_GAME_OVER    = "game_over"


class Tile:
    PHASE_IDLE   = "idle"
    PHASE_SHRINK = "shrink"
    PHASE_EXPAND = "expand"
    FLIP_SPEED   = 10

    def __init__(self, index, color, cx, cy, radius=32):
        self.index       = index
        self.color       = color
        self.cx          = cx
        self.cy          = cy
        self.radius      = radius
        self.base_radius = radius
        self.is_revealed = False
        self.is_matched  = False
        self.anim_phase  = self.PHASE_IDLE
        self.anim_radius = radius
        self.reveal_target = False
        self.glow_timer  = 0.0

    def start_flip(self, reveal: bool):
        self.anim_phase    = self.PHASE_SHRINK
        self.reveal_target = reveal

    def update(self, dt: float):
        if self.anim_phase == self.PHASE_SHRINK:
            self.anim_radius -= self.FLIP_SPEED
            if self.anim_radius <= 0:
                self.anim_radius = 0
                self.is_revealed = self.reveal_target
                self.anim_phase  = self.PHASE_EXPAND

        elif self.anim_phase == self.PHASE_EXPAND:
            self.anim_radius += self.FLIP_SPEED
            if self.anim_radius >= self.base_radius:
                self.anim_radius = self.base_radius
                self.anim_phase  = self.PHASE_IDLE

        if self.is_matched:
            self.glow_timer = (self.glow_timer + dt * 2.5) % (2 * math.pi)

    @property
    def is_animating(self):
        return self.anim_phase != self.PHASE_IDLE

    @property
    def glow_alpha(self):
        return 0.55 + 0.45 * math.sin(self.glow_timer)


class Game:
    FLIP_BACK_DELAY = 1.2
    AI_THINK_DELAY  = 0.6
    AI_FLIP2_DELAY  = 0.45

    def __init__(self, screen_w, screen_h):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.ai       = AIPlayer()
        self.reset()

    def reset(self):
        self.ai.reset()
        colors = TILE_COLORS * 2
        random.shuffle(colors)

        cx     = self.screen_w / 2
        cy     = self.screen_h / 2 - 20
        ring_r1 = min(self.screen_w, self.screen_h) * 0.22
        ring_r2 = min(self.screen_w, self.screen_h) * 0.38
        n_per_ring = 12

        self.tiles: list[Tile] = []
        # Inner Ring
        for i in range(n_per_ring):
            angle = math.radians(-90 + i * (360 / n_per_ring))
            tx = cx + ring_r1 * math.cos(angle)
            ty = cy + ring_r1 * math.sin(angle)
            self.tiles.append(Tile(len(self.tiles), colors[len(self.tiles)], tx, ty, radius=34))
        
        # Outer Ring
        for i in range(n_per_ring):
            angle = math.radians(-90 + (i + 0.5) * (360 / n_per_ring)) # Offset outer ring
            tx = cx + ring_r2 * math.cos(angle)
            ty = cy + ring_r2 * math.sin(angle)
            self.tiles.append(Tile(len(self.tiles), colors[len(self.tiles)], tx, ty, radius=34))

        self.player_score    = 0
        self.ai_score        = 0
        self.state           = STATE_PLAYER_TURN
        self.selected        = []          # face-up unmatched this turn
        self.flip_timer      = 0.0
        self.ai_timer        = 0.0
        self.ai_pending      = []
        self.ai_flip_stage   = 0
        self.player_was_last = True        # whose turn just ended (for flip-back routing)
        self.winner          = None

    # ── Public update ─────────────────────────────────────
    def update(self, dt: float):
        for tile in self.tiles:
            tile.update(dt)

        if self.state == STATE_FLIP_BACK:
            self.flip_timer -= dt
            if self.flip_timer <= 0:
                self._do_flip_back()

        elif self.state == STATE_AI_THINKING:
            self._update_ai(dt)

    # ── Player click ──────────────────────────────────────
    def handle_click(self, mx, my):
        if self.state != STATE_PLAYER_TURN:
            return
        if any(t.is_animating for t in self.tiles):
            return

        idx = self._tile_at(mx, my)
        if idx is None or self.tiles[idx].is_matched or self.tiles[idx].is_revealed:
            return
        if idx in self.selected:
            return

        tile = self.tiles[idx]
        tile.is_revealed = True
        tile.start_flip(reveal=True)
        self.ai.observe(idx, tile.color)
        self.selected.append(idx)

        if len(self.selected) == 2:
            self.player_was_last = True
            self._evaluate_pair(is_player=True)

    # ── Helpers ───────────────────────────────────────────
    def _tile_at(self, mx, my):
        for tile in self.tiles:
            if not tile.is_matched and not tile.is_revealed:
                if math.hypot(mx - tile.cx, my - tile.cy) <= tile.base_radius:
                    return tile.index
        return None

    def _evaluate_pair(self, is_player: bool):
        idx0, idx1 = self.selected[0], self.selected[1]
        t0, t1     = self.tiles[idx0], self.tiles[idx1]

        if t0.color == t1.color:
            # Match!
            t0.is_matched = True
            t1.is_matched = True
            self.ai.forget_tile(idx0)
            self.ai.forget_tile(idx1)

            if is_player:
                self.player_score += 1
            else:
                self.ai_score += 1

            self.selected = []

            if self._all_matched():
                self._end_game()
                return

            # Scorer gets another turn
            if is_player:
                self.state = STATE_PLAYER_TURN
            else:
                self._start_ai_turn()
        else:
            # No match — schedule flip-back
            self.flip_timer      = self.FLIP_BACK_DELAY
            self.state           = STATE_FLIP_BACK

    def _do_flip_back(self):
        for idx in self.selected:
            self.tiles[idx].start_flip(reveal=False)
        self.selected = []
        # Alternate turn
        if self.player_was_last:
            self._start_ai_turn()
        else:
            self.state = STATE_PLAYER_TURN

    def _start_ai_turn(self):
        self.state         = STATE_AI_THINKING
        self.ai_timer      = self.AI_THINK_DELAY
        self.ai_flip_stage = 0

    def _all_matched(self):
        return all(t.is_matched for t in self.tiles)

    def _end_game(self):
        self.state  = STATE_GAME_OVER
        if self.player_score > self.ai_score:
            self.winner = "player"
        elif self.ai_score > self.player_score:
            self.winner = "ai"
        else:
            self.winner = "draw"

    # ── AI state machine ──────────────────────────────────
    def _update_ai(self, dt: float):
        if any(t.is_animating for t in self.tiles):
            return

        if self.ai_flip_stage == 0:
            available = [t.index for t in self.tiles
                         if not t.is_matched and not t.is_revealed]
            if len(available) < 2:
                self.state = STATE_PLAYER_TURN
                return
            first, second      = self.ai.choose_moves(available)
            self.ai_pending    = [first, second]
            self.ai_timer      = self.AI_THINK_DELAY
            self.ai_flip_stage = 1

        elif self.ai_flip_stage == 1:
            self.ai_timer -= dt
            if self.ai_timer <= 0:
                idx = self.ai_pending[0]
                t   = self.tiles[idx]
                t.is_revealed = True
                t.start_flip(reveal=True)
                self.ai.observe(idx, t.color)
                self.selected      = [idx]
                self.ai_timer      = self.AI_FLIP2_DELAY
                self.ai_flip_stage = 2

        elif self.ai_flip_stage == 2:
            self.ai_timer -= dt
            if self.ai_timer <= 0:
                idx = self.ai_pending[1]
                t   = self.tiles[idx]
                t.is_revealed = True
                t.start_flip(reveal=True)
                self.ai.observe(idx, t.color)
                self.selected.append(idx)
                self.ai_timer      = 0.4
                self.ai_flip_stage = 3

        elif self.ai_flip_stage == 3:
            self.ai_timer -= dt
            if self.ai_timer <= 0:
                self.player_was_last = False
                self._evaluate_pair(is_player=False)
                self.ai_flip_stage = 0

    # ── Read-only state ───────────────────────────────────
    @property
    def turn_label(self):
        if self.state == STATE_GAME_OVER:
            return "GAME OVER"
        if self.state == STATE_PLAYER_TURN:
            return "PLAYER TURN"
        if self.state in (STATE_AI_THINKING, STATE_FLIP_BACK):
            if not self.player_was_last or self.state == STATE_AI_THINKING:
                return "AI TURN"
        return "AI TURN" if not self.player_was_last else "PLAYER TURN"
