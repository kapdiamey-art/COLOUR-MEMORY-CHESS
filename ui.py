import pygame
import math
import random

# ── Screens ──────────────────────────────────────────────
SCREEN_NAME_INPUT   = "name_input"
SCREEN_MENU         = "menu"
SCREEN_GAME         = "game"
SCREEN_RULES        = "rules"
SCREEN_SETTINGS     = "settings"
SCREEN_GAMEOVER     = "gameover"
SCREEN_PAUSE        = "pause"
SCREEN_SAVE         = "save"
SCREEN_LOAD         = "load"
SCREEN_HISTORY      = "history"
SCREEN_EXIT_CONFIRM = "exit_confirm"

# ── Palette (Premium Deep Themes) ────────────────────────
C_BG_TOP    = (15,  20,  50)   # Deep Indigo
C_BG_BOT    = (5,   5,   15)   # Midnight Black
C_TILE_DARK = (45,  55,  85)   # Deep Slate Blue
C_TILE_EDGE = (75,  95, 145)
C_GOLD      = (255, 205,  60)
C_PLAYER    = (70, 150, 255)
C_AI        = (255,  70,  90)
C_TEXT      = (230, 240, 255)
C_DIM       = (130, 150, 190)
C_WHITE     = (255, 255, 255)
C_BLACK     = (0,   0,   0)
C_ACCENT    = (110, 90, 255)
C_SUCCESS   = (60, 180, 80)
C_DANGER    = (200, 50, 70)

# ── Assets Cache ──────────────────────────────────────────
_font_cache = {}

def get_font(size, bold=False):
    key = (size, bold)
    if key not in _font_cache:
        # High-clarity and emoji-capable fonts
        fonts = ["Segoe UI Emoji", "Segoe UI Symbol", "Verdana", "Tahoma", "Arial"]
        font_path = None
        for f in fonts:
            font_path = pygame.font.match_font(f)
            if font_path: break
        
        try:
            if font_path:
                _font_cache[key] = pygame.font.Font(font_path, size)
            else:
                _font_cache[key] = pygame.font.SysFont("Arial", size, bold=bold)
        except:
            _font_cache[key] = pygame.font.Font(None, size)
    return _font_cache[key]

# ═══════════════════════════════════════════════════════════
# Components
# ═══════════════════════════════════════════════════════════

class Button:
    def __init__(self, cx, cy, w, h, label, color=C_PLAYER, font=None, icon=None):
        self.rect = pygame.Rect(0, 0, w, h)
        self.rect.center = (cx, cy)
        self.label = label
        self.color = color
        self.font = font
        self.icon = icon
        self.hovered = False
        self.scale = 1.0
        self._press_t = 0.0

    def update(self, mx, my, dt):
        self.hovered = self.rect.collidepoint(mx, my)
        if self._press_t > 0:
            self._press_t -= dt * 7
            self.scale = 1.0 - 0.08 * max(0, self._press_t)
        else: self.scale = 1.0

    def on_click(self, mx, my):
        if self.rect.collidepoint(mx, my):
            self._press_t = 1.0
            return True
        return False

    def draw(self, surf):
        r = self.rect
        if self.scale != 1.0:
            sw, sh = int(r.w * self.scale), int(r.h * self.scale)
            r2 = pygame.Rect(0, 0, sw, sh); r2.center = r.center
        else: r2 = r

        if self.hovered:
            glow = pygame.Surface((r2.w+40, r2.h+40), pygame.SRCALPHA)
            pygame.draw.rect(glow, (*self.color, 60), glow.get_rect(), border_radius=22)
            surf.blit(glow, (r2.x-20, r2.y-20))

        # Body with gradient-like shading
        pygame.draw.rect(surf, self.color, r2, border_radius=12)
        pygame.draw.rect(surf, (min(255, self.color[0]+40), min(255, self.color[1]+40), min(255, self.color[2]+40)), r2, width=2, border_radius=12)
        
        # Shine
        shine = pygame.Surface((r2.w, r2.h//2), pygame.SRCALPHA)
        shine.fill((255,255,255,20))
        surf.blit(shine, (r2.x, r2.y))

        if self.font:
            full_text = f"{self.icon} {self.label}" if self.icon else self.label
            txt = self.font.render(full_text, True, C_WHITE)
            surf.blit(txt, txt.get_rect(center=r2.center))

class Slider:
    def __init__(self, cx, cy, w, label, value=0.5):
        self.rect = pygame.Rect(cx - w//2, cy, w, 10)
        self.label = label
        self.value = value
        self.dragging = False

    def update(self, mx, my, clicked):
        if clicked and self.rect.inflate(0, 30).collidepoint(mx, my):
            self.dragging = True
        if not clicked: self.dragging = False
        
        if self.dragging:
            self.value = max(0, min(1, (mx - self.rect.x) / self.rect.w))

    def draw(self, surf):
        pygame.draw.rect(surf, C_TILE_DARK, self.rect, border_radius=5)
        fill_w = int(self.rect.w * self.value)
        if fill_w > 0:
            pygame.draw.rect(surf, C_PLAYER, (self.rect.x, self.rect.y, fill_w, 10), border_radius=5)
        
        handle_x = self.rect.x + fill_w
        pygame.draw.circle(surf, C_WHITE, (handle_x, self.rect.centery), 10)
        pygame.draw.circle(surf, C_GOLD, (handle_x, self.rect.centery), 6)
        
        f = get_font(18)
        txt = f.render(f"{self.label}: {int(self.value * 100)}%", True, C_TEXT)
        surf.blit(txt, txt.get_rect(midleft=(self.rect.x, self.rect.y - 25)))

class ParticleSystem:
    def __init__(self, w, h, count=80):
        self.w, self.h = w, h
        self.particles = [{"x": random.random()*w, "y": random.random()*h, 
                           "r": random.random()*3, "vx": random.uniform(-0.4, 0.4), 
                           "vy": random.uniform(-0.6, -0.2), "alpha": random.randint(30, 120),
                           "col": random.choice([C_PLAYER, C_AI, C_GOLD])} for _ in range(count)]

    def update(self):
        for p in self.particles:
            p["x"] += p["vx"]; p["y"] += p["vy"]
            if p["y"] < -10: p["y"] = self.h + 10; p["x"] = random.random()*self.w

    def draw(self, surf):
        for p in self.particles:
            s = pygame.Surface((int(p["r"]*4), int(p["r"]*4)), pygame.SRCALPHA)
            pygame.draw.circle(s, (*p["col"], p["alpha"]), (int(p["r"]*2), int(p["r"]*2)), int(p["r"]))
            surf.blit(s, (int(p["x"]), int(p["y"])))

# ═══════════════════════════════════════════════════════════
# Drawing Helpers
# ═══════════════════════════════════════════════════════════

def draw_gradient_bg(surf):
    w, h = surf.get_size()
    for y in range(h):
        t = y / h
        r = int(C_BG_TOP[0] + (C_BG_BOT[0]-C_BG_TOP[0])*t)
        g = int(C_BG_TOP[1] + (C_BG_BOT[1]-C_BG_TOP[1])*t)
        b = int(C_BG_TOP[2] + (C_BG_BOT[2]-C_BG_TOP[2])*t)
        pygame.draw.line(surf, (r,g,b), (0,y), (w,y))

def draw_card(surf, cx, cy, w, h, alpha=240, title=""):
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(s, (20, 30, 60, alpha), s.get_rect(), border_radius=32)
    pygame.draw.rect(s, (100, 120, 180, 180), s.get_rect(), width=3, border_radius=32)
    surf.blit(s, (cx-w//2, cy-h//2))
    if title:
        f = get_font(36, bold=True)
        draw_text_glow(surf, title, f, C_GOLD, cx, cy - h//2 + 50)

def draw_text_glow(surf, text, font, color, cx, cy, glow_color=None, glow_r=2):
    """Draws a sharp shadow/glow effect for better legibility."""
    if glow_color is None: glow_color = (0, 0, 0)
    if glow_r > 0:
        t2 = font.render(text, True, (*glow_color, 150))
        surf.blit(t2, t2.get_rect(center=(cx + glow_r, cy + glow_r)))
    t = font.render(text, True, color)
    surf.blit(t, t.get_rect(center=(cx, cy)))

def draw_pawn(surf, cx, cy, r, color, is_matched=False):
    c_dark = [max(0, c - 50) for c in color]
    c_light = [min(255, c + 70) for c in color]
    # Base
    pygame.draw.ellipse(surf, c_dark, (cx - r*0.8, cy + r*0.4, r*1.6, r*0.5))
    pygame.draw.ellipse(surf, color, (cx - r*0.7, cy + r*0.35, r*1.4, r*0.45))
    # Body
    pts = [(cx-r*0.5, cy+r*0.5), (cx+r*0.5, cy+r*0.5), (cx+r*0.2, cy-r*0.3), (cx-r*0.2, cy-r*0.3)]
    pygame.draw.polygon(surf, color, pts)
    # Head
    pygame.draw.circle(surf, color, (int(cx), int(cy - r*0.6)), int(r*0.5))
    if not is_matched:
        pygame.draw.circle(surf, (255,255,255,100), (int(cx-r*0.2), int(cy-r*0.7)), int(r*0.15))

def draw_tile(surf, tile):
    cx, cy, ar = int(tile.cx), int(tile.cy), int(tile.anim_radius)
    if ar <= 0: return
    if tile.is_matched:
        draw_glow(surf, cx, cy, ar, C_GOLD, alpha=int(120 + 80*tile.glow_alpha))
        draw_pawn(surf, cx, cy, ar, tile.color, is_matched=True)
    elif tile.is_revealed:
        draw_glow(surf, cx, cy, ar, tile.color, alpha=100)
        draw_pawn(surf, cx, cy, ar, tile.color)
    else:
        draw_pawn(surf, cx, cy, ar, C_TILE_DARK)
        pygame.draw.circle(surf, C_TILE_EDGE, (cx, int(cy - ar*0.6)), int(ar*0.4), width=2)

def draw_glow(surf, cx, cy, r, color, alpha=100):
    for i in range(3):
        rad = r + (i+1)*8
        s = pygame.Surface((rad*2, rad*2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*color, alpha // (i+1)), (rad, rad), rad)
        surf.blit(s, (cx-rad, cy-rad))

# ═══════════════════════════════════════════════════════════
# Screen Renderers
# ═══════════════════════════════════════════════════════════

def draw_name_input(surf, buttons, name_text):
    w, h = surf.get_size()
    draw_card(surf, w//2, h//2, w-60, 400, title="WELCOME! 👋")
    f = get_font(24)
    draw_text_glow(surf, "Enter Your Name:", f, C_TEXT, w//2, h//2 - 60)
    
    # Input Box
    box = pygame.Rect(w//2 - 200, h//2, 400, 60)
    pygame.draw.rect(surf, C_BLACK, box, border_radius=15)
    pygame.draw.rect(surf, C_PLAYER, box, width=2, border_radius=15)
    
    txt = f.render(name_text + "|", True, C_WHITE)
    surf.blit(txt, txt.get_rect(center=box.center))
    
    for b in buttons: b.draw(surf)

def draw_menu(surf, buttons, title_t):
    w, h = surf.get_size()
    cx, cy = w//2, h//6
    # Title
    f_big = get_font(64, bold=True)
    draw_text_glow(surf, "COLOR MEMORY", f_big, C_WHITE, cx, cy, glow_color=C_PLAYER, glow_r=4)
    draw_text_glow(surf, "CHESS 🏆", f_big, C_GOLD, cx, cy + 70, glow_color=C_ACCENT, glow_r=4)
    
    # Decorative
    draw_glow(surf, w//2, h//2 - 120, 70, C_GOLD, alpha=30)
    draw_pawn(surf, w//2, h//2 - 120, 60, C_GOLD)

    for btn in buttons: btn.draw(surf)

def draw_player_card(surf, cx, cy, w, name, score, color, is_ai=False):
    h = 110
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(s, (25, 35, 65, 240), s.get_rect(), border_radius=24)
    pygame.draw.rect(s, (*color, 150), s.get_rect(), width=3, border_radius=24)
    
    # Avatar Circle
    pygame.draw.circle(s, (*color, 60), (55, h//2), 40)
    pygame.draw.circle(s, color, (55, h//2), 40, width=2)
    icon = "🤖" if is_ai else "👤"
    f_icon = get_font(38)
    it = f_icon.render(icon, True, C_WHITE)
    s.blit(it, it.get_rect(center=(55, h//2)))

    # Name & Rank
    f_name = get_font(28, bold=True)
    nt = f_name.render(f"{name} {'🤖' if is_ai else '⭐'}", True, C_WHITE)
    s.blit(nt, (110, 25))
    
    f_rank = get_font(16)
    rt = f_rank.render("Grandmaster" if not is_ai else "Super Computer", True, C_DIM)
    s.blit(rt, (110, 62))

    # Score
    f_score = get_font(48, bold=True)
    st = f_score.render(str(score), True, color)
    s.blit(st, st.get_rect(midright=(w - 30, h//2)))

    surf.blit(s, (cx - w//2, cy - h//2))

def draw_game_screen(surf, game, buttons):
    w, h = surf.get_size()
    
    # Active Turn highlighting
    p_active = "PLAYER" in game.turn_label
    ai_active = "AI" in game.turn_label
    
    # Top Player Card
    draw_player_card(surf, w//2, 110, w - 50, game.player_name, game.player_score, C_PLAYER if p_active else C_DIM)
    
    # Turn Indicator Badge (Side)
    tl = game.turn_label
    tc = C_PLAYER if p_active else (C_AI if ai_active else C_GOLD)
    f_turn = get_font(22, bold=True)
    
    # Small Vertical Badge at the right
    badge_w, badge_h = 40, 180
    badge_rect = pygame.Rect(w - 45, h//2 - badge_h//2, badge_w, badge_h)
    pygame.draw.rect(surf, (20, 30, 60, 200), badge_rect, border_radius=10)
    pygame.draw.rect(surf, tc, badge_rect, width=2, border_radius=10)
    
    # Draw vertical text
    for i, char in enumerate(tl.replace(" TURN", "")):
        ct = f_turn.render(char, True, tc)
        surf.blit(ct, ct.get_rect(center=(badge_rect.centerx, badge_rect.y + 30 + i*25)))

    # Board Decorations
    bcx, bcy = w//2, h//2 + 30
    for r in [w*0.22, w*0.38, w*0.52]:
        pygame.draw.circle(surf, (100, 120, 200, 30), (bcx, bcy), int(r), width=3)
    
    for tile in game.tiles: draw_tile(surf, tile)

    # Bottom AI Card
    draw_player_card(surf, w//2, h - 150, w - 50, "AI Master", game.ai_score, C_AI if ai_active else C_DIM, is_ai=True)

    # Stats
    f_stats = get_font(16)
    st_txt = f_stats.render(f"Moves: {game.total_moves} ⏱️ Time: {game.total_time}s", True, C_DIM)
    surf.blit(st_txt, st_txt.get_rect(center=(w//2, h - 70)))

    for btn in buttons: btn.draw(surf)

def draw_pause_menu(surf, buttons, sliders):
    w, h = surf.get_size()
    draw_card(surf, w//2, h//2, w-70, 600, title="PAUSED ⏸️")
    for s in sliders: s.draw(surf)
    for b in buttons: b.draw(surf)

def draw_save_game(surf, buttons, input_text):
    w, h = surf.get_size()
    draw_card(surf, w//2, h//2, w-70, 520, title="SAVE GAME 💾")
    f = get_font(24)
    box = pygame.Rect(w//2 - 160, h//2 - 60, 320, 55)
    pygame.draw.rect(surf, C_BLACK, box, border_radius=12)
    pygame.draw.rect(surf, C_TILE_EDGE, box, width=2, border_radius=12)
    txt = f.render(input_text + "|", True, C_WHITE)
    surf.blit(txt, txt.get_rect(center=box.center))
    for b in buttons: b.draw(surf)

def draw_saved_games(surf, buttons, saves):
    w, h = surf.get_size()
    draw_card(surf, w//2, h//2, w-50, 620, title="SAVED GAMES 💾")
    if not saves:
        f = get_font(22)
        t = f.render("No saves found. 📭", True, C_DIM)
        surf.blit(t, t.get_rect(center=(w//2, h//2)))
    for b in buttons: b.draw(surf)

def draw_game_history(surf, buttons, history):
    w, h = surf.get_size()
    draw_card(surf, w//2, h//2, w-40, 680, title="HISTORY 📜")
    if not history:
        f = get_font(22)
        t = f.render("No battles yet! ⚔️", True, C_DIM)
        surf.blit(t, t.get_rect(center=(w//2, h//2)))
    else:
        f = get_font(16)
        for i, entry in enumerate(history[-12:]):
            y = h//2 - 240 + i * 40
            # Format date
            date_str = str(entry['date'])[:16] # YYYY-MM-DD HH:MM
            # Format score
            p_score = entry.get('player_score', 0)
            a_score = entry.get('ai_score', 0)
            score_str = f"{p_score}-{a_score}"
            
            winner = entry['winner'].upper()
            txt = f"📅 {date_str} - {winner} WON ({score_str})"
            col = C_PLAYER if entry['winner'] == 'player' else C_AI
            st = f.render(txt, True, col)
            surf.blit(st, st.get_rect(center=(w//2, y)))
    for b in buttons: b.draw(surf)

def draw_settings(surf, buttons, sliders, difficulty):
    w, h = surf.get_size()
    draw_card(surf, w//2, h//2, w-70, 580, title="SETTINGS ⚙️")
    for s in sliders: s.draw(surf)
    f = get_font(22)
    surf.blit(f.render(f"Difficulty: {difficulty.upper()} 🧠", True, C_GOLD), (w//2 - 160, h//2 + 60))
    for b in buttons: b.draw(surf)

def draw_rules(surf, back_btn):
    w, h = surf.get_size()
    draw_card(surf, w//2, h//2, w-50, 580, title="RULES 📖")
    rules = [
        "1. Select 2 hidden pieces. ♟️",
        "2. Match colors to score! ✨",
        "3. AI remembers everything! 🧠",
        "4. Most matches win! 🏆",
        "5. Alternate turns. 🔄"
    ]
    f = get_font(22)
    for i, r in enumerate(rules):
        rt = f.render(r, True, C_TEXT)
        surf.blit(rt, (w//2 - 170, h//2 - 140 + i*60))
    back_btn.draw(surf)

def draw_gameover(surf, game, buttons):
    w, h = surf.get_size()
    draw_card(surf, w//2, h//2, w-60, 580, title="GAME OVER 🏁")
    f_res = get_font(48, bold=True)
    if game.winner == "player": draw_text_glow(surf, "VICTORY! 🎉", f_res, C_PLAYER, w//2, h//2 - 140)
    elif game.winner == "ai": draw_text_glow(surf, "AI WON! 💀", f_res, C_AI, w//2, h//2 - 140)
    else: draw_text_glow(surf, "STALEMATE 🤝", f_res, C_GOLD, w//2, h//2 - 140)
    f_stats = get_font(22)
    stats = [
        f"Matches: {game.correct_matches} ✨",
        f"Final Score: {game.player_score} - {game.ai_score} 🏆"
    ]
    for i, s in enumerate(stats):
        st = f_stats.render(s, True, C_TEXT)
        surf.blit(st, st.get_rect(center=(w//2, h//2 - 30 + i*45)))
    for b in buttons: b.draw(surf)

def draw_confirm_exit(surf, buttons):
    w, h = surf.get_size()
    draw_card(surf, w//2, h//2, w-90, 340, title="EXIT? 🚪")
    f = get_font(22)
    t = f.render("Finished for now? 👋", True, C_TEXT)
    surf.blit(t, t.get_rect(center=(w//2, h//2 - 10)))
    for b in buttons: b.draw(surf)
