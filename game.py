import random
import math
import time
from ai_engine import AIEngine
from game_state import GameState

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
        self.glow_timer += dt * 3
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
                self.anim_phase = self.PHASE_IDLE

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
        self.ai_engine = AIEngine("ALPHA-BETA")
        self.ai_memory = {}
        self.player_name = "Player"
        self.reset()

    def reset(self):
        self.ai_memory = {}
        colors = TILE_COLORS * 2
        random.shuffle(colors)
        cx, cy = self.screen_w / 2, self.screen_h / 2 + 30
        ring_radii = [min(W, H)*0.15, min(W, H)*0.28, min(W, H)*0.41] if 'W' in globals() else [80, 150, 220]
        ring_counts = [4, 8, 12]
        self.tiles = []
        c_idx = 0
        for r_idx, radius in enumerate(ring_radii):
            for i in range(ring_counts[r_idx]):
                angle = (2 * math.pi * i) / ring_counts[r_idx]
                self.tiles.append(Tile(len(self.tiles), colors[c_idx], cx + radius*math.cos(angle), cy + radius*math.sin(angle)))
                c_idx += 1
        self.player_score = 0
        self.ai_score = 0
        self.state = STATE_PLAYER_TURN
        self.selected = []
        self.flip_timer = 0
        self.player_was_last = False
        self.winner = None
        self.total_moves = 0
        self.correct_matches = 0
        self.start_time = time.time()
        self.total_time = 0
        self.sound_trigger = None
        self.ai_flip_stage = 0

    def update(self, dt: float):
        if self.state == STATE_GAME_OVER: return
        for t in self.tiles: t.update(dt)
        if self.state in (STATE_AI_THINKING, STATE_AI_TURN): self._update_ai(dt)
        elif self.state == STATE_FLIP_BACK:
            self.flip_timer -= dt
            if self.flip_timer <= 0:
                self._do_flip_back()
                self.sound_trigger = "move"
        if all(t.is_matched for t in self.tiles) and self.state != STATE_GAME_OVER: self._end_game()

    def handle_click(self, mx, my):
        if self.state != STATE_PLAYER_TURN or any(t.is_animating() for t in self.tiles): return False
        idx = self._tile_at(mx, my)
        if idx is None or self.tiles[idx].is_matched or self.tiles[idx].is_revealed or idx in self.selected: return False
        t = self.tiles[idx]
        t.is_revealed = True; t.start_flip(reveal=True)
        self.ai_memory[idx] = t.color
        self.selected.append(idx)
        self.sound_trigger = "move"
        if len(self.selected) == 2:
            self.total_moves += 1; self.player_was_last = True
            self._evaluate_pair(is_player=True)
        return True

    def _tile_at(self, mx, my):
        for t in self.tiles:
            if not t.is_matched and not t.is_revealed:
                if math.hypot(mx - t.cx, my - t.cy) <= t.base_radius: return t.index
        return None

    def _evaluate_pair(self, is_player: bool):
        t0, t1 = self.tiles[self.selected[0]], self.tiles[self.selected[1]]
        if t0.color == t1.color:
            t0.is_matched = t1.is_matched = True
            if is_player: self.player_score += 1; self.correct_matches += 1
            else: self.ai_score += 1
            self.selected = []
            if not is_player: self._start_ai_turn()
        else:
            self.flip_timer = self.FLIP_BACK_DELAY; self.state = STATE_FLIP_BACK

    def _do_flip_back(self):
        for idx in self.selected: self.tiles[idx].start_flip(reveal=False)
        self.selected = []
        if self.player_was_last: self._start_ai_turn()
        else: self.state = STATE_PLAYER_TURN

    def _start_ai_turn(self):
        self.state = STATE_AI_THINKING; self.ai_timer = self.AI_THINK_DELAY; self.ai_flip_stage = 0

    def _end_game(self):
        self.state = STATE_GAME_OVER; self.total_time = int(time.time() - self.start_time)
        if self.player_score > self.ai_score: self.winner = "player"
        elif self.ai_score > self.player_score: self.winner = "ai"
        else: self.winner = "draw"

    def _update_ai(self, dt: float):
        if any(t.is_animating() for t in self.tiles): return
        if self.ai_flip_stage == 0:
            tiles_data = []
            for t in self.tiles:
                # AI only 'knows' colors that are in its memory or already matched
                color = t.color if (t.index in self.ai_memory or t.is_matched) else None
                tiles_data.append({
                    "index": t.index, 
                    "color": color, 
                    "is_matched": t.is_matched, 
                    "is_revealed": t.is_revealed
                })
                
            state = GameState(tiles_data, self.ai_memory, self.ai_score, self.player_score, player_turn=False)
            move = self.ai_engine.get_best_move(state)
            if not move: 
                avail = [t.index for t in self.tiles if not t.is_matched and not t.is_revealed]
                if len(avail) >= 2: 
                    move = tuple(random.sample(avail, 2))
                else: 
                    self.state = STATE_PLAYER_TURN
                    return
            self.ai_pending = list(move); self.ai_timer = self.AI_THINK_DELAY; self.ai_flip_stage = 1
        elif self.ai_flip_stage == 1:
            self.ai_timer -= dt
            if self.ai_timer <= 0:
                idx = self.ai_pending[0]; t = self.tiles[idx]
                t.is_revealed = True; t.start_flip(reveal=True)
                self.ai_memory[idx] = t.color; self.selected = [idx]
                self.ai_timer = self.AI_FLIP2_DELAY; self.ai_flip_stage = 2; self.sound_trigger = "move"
        elif self.ai_flip_stage == 2:
            self.ai_timer -= dt
            if self.ai_timer <= 0:
                idx = self.ai_pending[1]; t = self.tiles[idx]
                t.is_revealed = True; t.start_flip(reveal=True)
                self.ai_memory[idx] = t.color; self.selected.append(idx)
                self.ai_timer = 0.4; self.ai_flip_stage = 3; self.sound_trigger = "move"
        elif self.ai_flip_stage == 3:
            self.ai_timer -= dt
            if self.ai_timer <= 0:
                self.total_moves += 1; self.player_was_last = False; self._evaluate_pair(is_player=False); self.ai_flip_stage = 0

    @property
    def turn_label(self):
        if self.state == STATE_GAME_OVER: return "GAME OVER"
        if self.state == STATE_PLAYER_TURN: return "PLAYER TURN"
        return "AI TURN"

    def serialize(self):
        return {
            "player_score": self.player_score, "ai_score": self.ai_score, "total_moves": self.total_moves,
            "correct_matches": self.correct_matches, "total_time": self.total_time, "state": self.state,
            "difficulty": self.ai_engine.difficulty,
            "tiles": [{"index": t.index, "color": t.color, "is_revealed": t.is_revealed, "is_matched": t.is_matched} for t in self.tiles],
            "ai_memory": self.ai_memory, "player_was_last": self.player_was_last
        }

    def deserialize(self, data):
        self.player_score = data["player_score"]; self.ai_score = data["ai_score"]
        self.total_moves = data["total_moves"]; self.correct_matches = data["correct_matches"]
        self.total_time = data["total_time"]; self.start_time = time.time() - self.total_time
        self.state = data["state"]; self.ai_memory = {int(k): tuple(v) for k, v in data["ai_memory"].items()}
        self.player_was_last = data["player_was_last"]
        if "difficulty" in data: self.ai_engine.difficulty = data["difficulty"]
        for i, t_data in enumerate(data["tiles"]):
            t = self.tiles[i]
            t.color = tuple(t_data["color"]) # Restore color!
            t.is_revealed = t_data["is_revealed"]; t.is_matched = t_data["is_matched"]
