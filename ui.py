"""
ui.py - Drawing, Screens, Buttons, Particles, Animations
"""

import pygame
import math
import random

# ── Screens ──────────────────────────────────────────────
SCREEN_MENU      = "menu"
SCREEN_GAME      = "game"
SCREEN_RULES     = "rules"
SCREEN_SETTINGS  = "settings"
SCREEN_GAMEOVER  = "gameover"

# ── Palette ──────────────────────────────────────────────
# ── Palette (Premium Deep Themes) ────────────────────────
C_BG_TOP    = (15,  25,  60)   # Deep Navy
C_BG_BOT    = (5,   8,   15)   # Almost Black Blue
C_TILE_DARK = (40,  50,  80)   # Blueish Grey
C_TILE_EDGE = (70,  90, 140)
C_GOLD      = (255, 200,  50)
C_PLAYER    = (80, 160, 255)
C_AI        = (255,  80, 100)
C_TEXT      = (240, 245, 255)
C_DIM       = (140, 160, 200)
C_WHITE     = (255, 255, 255)
C_BLACK     = (0,   0,   0)
C_ACCENT    = (120, 100, 255)


# ═══════════════════════════════════════════════════════════
# Particles
# ═══════════════════════════════════════════════════════════
class Particle:
    def __init__(self, w, h):
        self.reset(w, h)

    def reset(self, w, h):
        self.x  = random.uniform(0, w)
        self.y  = random.uniform(0, h)
        self.r  = random.uniform(1, 3)
        self.vx = random.uniform(-0.3, 0.3)
        self.vy = random.uniform(-0.5, -0.1)
        self.alpha = random.randint(40, 130)
        self.col = random.choice([C_PLAYER, C_AI, C_GOLD, (180,180,255)])

    def update(self, w, h):
        self.x += self.vx
        self.y += self.vy
        if self.y < -5 or self.x < -5 or self.x > w+5:
            self.reset(w, h)
            self.y = h + 5


class ParticleSystem:
    def __init__(self, w, h, count=60):
        self.w = w
        self.h = h
        self.particles = [Particle(w, h) for _ in range(count)]

    def update(self):
        for p in self.particles:
            p.update(self.w, self.h)

    def draw(self, surf):
        for p in self.particles:
            s = pygame.Surface((int(p.r*2+2), int(p.r*2+2)), pygame.SRCALPHA)
            pygame.draw.circle(s, (*p.col, p.alpha), (int(p.r+1), int(p.r+1)), int(p.r))
            surf.blit(s, (int(p.x - p.r), int(p.y - p.r)))


# ═══════════════════════════════════════════════════════════
# Button
# ═══════════════════════════════════════════════════════════
class Button:
    def __init__(self, cx, cy, w, h, label, color=C_PLAYER, font=None):
        self.rect   = pygame.Rect(0, 0, w, h)
        self.rect.center = (cx, cy)
        self.label  = label
        self.color  = color
        self.font   = font
        self.hovered = False
        self.scale   = 1.0          # for press animation
        self._press_t = 0.0

    def update(self, mx, my, dt):
        self.hovered = self.rect.collidepoint(mx, my)
        if self._press_t > 0:
            self._press_t -= dt * 6
            self.scale = 1.0 - 0.08 * max(0, self._press_t)
        else:
            self.scale = 1.0

    def on_click(self, mx, my):
        if self.rect.collidepoint(mx, my):
            self._press_t = 1.0
            return True
        return False

    def draw(self, surf):
        r = self.rect
        if self.scale != 1.0:
            sw = int(r.w * self.scale)
            sh = int(r.h * self.scale)
            r2 = pygame.Rect(0, 0, sw, sh)
            r2.center = r.center
        else:
            r2 = r

        # Glow behind button when hovered
        if self.hovered:
            glow = pygame.Surface((r2.w+30, r2.h+30), pygame.SRCALPHA)
            pygame.draw.rect(glow, (*self.color, 55), glow.get_rect(), border_radius=22)
            surf.blit(glow, (r2.x-15, r2.y-15))

        # Button body
        pygame.draw.rect(surf, self.color, r2, border_radius=16)
        # Highlight strip
        hl = pygame.Surface((r2.w-8, r2.h//2-4), pygame.SRCALPHA)
        hl.fill((255,255,255,25))
        surf.blit(hl, (r2.x+4, r2.y+4))
        # Border
        bc = (min(self.color[0]+60,255), min(self.color[1]+60,255), min(self.color[2]+60,255))
        pygame.draw.rect(surf, bc, r2, width=2, border_radius=16)

        if self.font:
            txt = self.font.render(self.label, True, C_WHITE)
            surf.blit(txt, txt.get_rect(center=r2.center))


# ═══════════════════════════════════════════════════════════
# Fonts helper
# ═══════════════════════════════════════════════════════════
_font_cache = {}

def get_font(size, bold=False):
    key = (size, bold)
    if key not in _font_cache:
        # Try a few fonts that are likely to have better emoji support on Windows
        fonts_to_try = ["Segoe UI Emoji", "Segoe UI Symbol", "Arial", "Consolas"]
        for f_name in fonts_to_try:
            try:
                _font_cache[key] = pygame.font.SysFont(f_name, size, bold=bold)
                # Test if font actually works by rendering a simple char
                _font_cache[key].render("A", True, (0,0,0))
                break
            except Exception:
                continue
        else:
            _font_cache[key] = pygame.font.Font(None, size)
    return _font_cache[key]


# ═══════════════════════════════════════════════════════════
# Drawing helpers
# ═══════════════════════════════════════════════════════════
def draw_gradient_bg(surf):
    w, h = surf.get_size()
    # Radial-ish gradient or complex linear
    for y in range(h):
        t = y / h
        r = int(C_BG_TOP[0] + (C_BG_BOT[0]-C_BG_TOP[0])*t)
        g = int(C_BG_TOP[1] + (C_BG_BOT[1]-C_BG_TOP[1])*t)
        b = int(C_BG_TOP[2] + (C_BG_BOT[2]-C_BG_TOP[2])*t)
        pygame.draw.line(surf, (r,g,b), (0,y), (w,y))
    
    # Add subtle circular grid pattern
    cx, cy = w//2, h//2 - 20
    for r in range(100, 800, 120):
        pygame.draw.circle(surf, (255, 255, 255, 10), (cx, cy), r, width=1)
    
    # Random stars/dots
    random.seed(42) # Deterministic stars
    for _ in range(100):
        sx = random.randint(0, w)
        sy = random.randint(0, h)
        sc = random.randint(30, 100)
        pygame.draw.circle(surf, (sc, sc, sc+50, 40), (sx, sy), 1)


def draw_glow_circle(surf, cx, cy, r, color, alpha=120):
    for dr in range(18, 0, -3):
        s = pygame.Surface((r*2+dr*4, r*2+dr*4), pygame.SRCALPHA)
        a = int(alpha * (1 - dr/20))
        pygame.draw.circle(s, (*color, a), (r+dr*2, r+dr*2), r+dr)
        surf.blit(s, (int(cx-r-dr*2), int(cy-r-dr*2)))


def draw_pawn(surf, cx, cy, r, color, is_matched=False):
    """Draws a procedurally generated chess pawn shape with shading."""
    # Main color with slight gradient feel
    c_dark = [max(0, c - 40) for c in color]
    c_light = [min(255, c + 60) for c in color]
    
    # Base
    base_w = r * 1.5
    base_h = r * 0.45
    pygame.draw.ellipse(surf, c_dark, (cx - base_w//2 + 2, cy + r*0.4 + 2, base_w, base_h))
    pygame.draw.ellipse(surf, color, (cx - base_w//2, cy + r*0.4, base_w, base_h))
    
    # Body
    body_points = [
        (cx - r*0.6, cy + r*0.6),
        (cx + r*0.6, cy + r*0.6),
        (cx + r*0.25, cy - r*0.3),
        (cx - r*0.25, cy - r*0.3),
    ]
    pygame.draw.polygon(surf, color, body_points)
    # Body Highlight
    pygame.draw.line(surf, c_light, (cx - r*0.2, cy + r*0.4), (cx - r*0.1, cy - r*0.2), width=3)
    
    # Neck
    pygame.draw.ellipse(surf, color, (cx - r*0.45, cy - r*0.4, r*0.9, r*0.25))
    
    # Head
    pygame.draw.circle(surf, color, (cx, cy - r*0.65), int(r*0.55))
    
    # Head Highlight
    if not is_matched:
        pygame.draw.circle(surf, (255,255,255,80), (int(cx - r*0.2), int(cy - r*0.8)), int(r*0.18))

def draw_tile(surf, tile, player_col=C_PLAYER):
    cx = int(tile.cx)
    cy = int(tile.cy)
    ar = int(tile.anim_radius)
    if ar <= 0:
        return

    if tile.is_matched:
        # Gold glow pulse (Circular as requested)
        ga = int(100 + 100 * tile.glow_alpha)
        draw_glow_circle(surf, cx, cy, ar, C_GOLD, alpha=ga)
        draw_pawn(surf, cx, cy, ar, tile.color, is_matched=True)
        # Crown outline
        pygame.draw.circle(surf, C_GOLD, (cx, cy - ar*0.65), int(ar*0.6), width=3)
    elif tile.is_revealed:
        # Circular glow
        draw_glow_circle(surf, cx, cy, ar, tile.color, alpha=90)
        draw_pawn(surf, cx, cy, ar, tile.color)
    else:
        # Hidden tile
        draw_pawn(surf, cx, cy, ar, C_TILE_DARK)
        pygame.draw.circle(surf, C_TILE_EDGE, (cx, cy - ar*0.65), int(ar*0.55), width=2)


def draw_text_glow(surf, text, font, color, cx, cy, glow_color=None, glow_r=3):
    if glow_color:
        for dx in range(-glow_r, glow_r+1, glow_r):
            for dy in range(-glow_r, glow_r+1, glow_r):
                if dx==0 and dy==0:
                    continue
                t2 = font.render(text, True, glow_color)
                surf.blit(t2, t2.get_rect(center=(cx+dx, cy+dy)))
    t = font.render(text, True, color)
    surf.blit(t, t.get_rect(center=(cx, cy)))


def draw_card(surf, cx, cy, w, h, alpha=200):
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(s, (20, 28, 52, alpha), s.get_rect(), border_radius=24)
    pygame.draw.rect(s, (60, 80, 140, 120), s.get_rect(), width=2, border_radius=24)
    surf.blit(s, (cx-w//2, cy-h//2))


# ═══════════════════════════════════════════════════════════
# Screen renderers
# ═══════════════════════════════════════════════════════════
def draw_menu(surf, buttons, title_t):
    w, h = surf.get_size()
    # Animated background effects for menu
    cx, cy = w//2, h//3
    
    # Floating particles specific to title
    for i in range(12):
        ang = title_t * 0.5 + i * (math.pi*2/12)
        px = cx + 220 * math.cos(ang)
        py = cy + 60 * math.sin(ang * 2)
        pygame.draw.circle(surf, (100, 150, 255, 40), (int(px), int(py)), 8)

    # Animated title glow pulse
    pulse = 0.8 + 0.2*math.sin(title_t*2.5)
    f_big  = get_font(62, bold=True)
    
    # Shadow layer
    draw_text_glow(surf, "👑  COLOR MEMORY", f_big, (10, 10, 30), w//2+4, cy-14, glow_r=0)
    
    # Main layers
    draw_glow_circle(surf, w//2, cy, int(100*pulse), C_PLAYER, alpha=int(100*pulse))
    draw_text_glow(surf, "👑  COLOR MEMORY", f_big, C_WHITE, w//2, cy-18,
                   glow_color=C_PLAYER, glow_r=6)
    draw_text_glow(surf, "♟️  CHESS", f_big, C_GOLD, w//2, cy+48,
                   glow_color=C_ACCENT, glow_r=6)
    
    t = get_font(18).render("A Masterful Strategy Memory Duel", True, C_DIM)
    surf.blit(t, t.get_rect(center=(w//2, cy+110)))
    for btn in buttons:
        btn.draw(surf)


def draw_rules(surf, back_btn):
    w, h = surf.get_size()
    draw_card(surf, w//2, h//2, 540, 380)
    f  = get_font(30, bold=True)
    fs = get_font(18)
    draw_text_glow(surf,"📜  HOW TO PLAY  📜", f, C_GOLD, w//2, h//2-145)
    rules = [
        "🔵  Click any 2 hidden tiles to reveal them.",
        "✅  Matching colors score a point — tiles stay revealed.",
        "❌  Non-matching tiles flip back after a short delay.",
        "🤖  The AI memorises every tile it has seen.",
        "🏆  Most matched pairs when board clears wins!",
        "🔄  Player and AI alternate turns.",
    ]
    for i, line in enumerate(rules):
        t = fs.render(line, True, C_TEXT)
        surf.blit(t, t.get_rect(midleft=(w//2-230, h//2-95+i*38)))
    back_btn.draw(surf)


def draw_settings(surf, toggle_btn, back_btn, ai_smart):
    w, h = surf.get_size()
    draw_card(surf, w//2, h//2, 440, 280)
    f  = get_font(30, bold=True)
    fs = get_font(18)
    draw_text_glow(surf, "⚙️  GAME PREFERENCES", f, C_GOLD, w//2, h//2-95)
    label = "AI Mode:  SMART" if ai_smart else "AI Mode:  RANDOM"
    col   = C_PLAYER if ai_smart else C_AI
    t = fs.render(label, True, col)
    surf.blit(t, t.get_rect(center=(w//2, h//2-20)))
    toggle_btn.draw(surf)
    back_btn.draw(surf)


def draw_gameover(surf, game, play_btn, menu_btn):
    w, h = surf.get_size()
    draw_card(surf, w//2, h//2, 460, 320)
    f_big = get_font(38, bold=True)
    f_med = get_font(22)
    f_sm  = get_font(18)

    if game.winner == "player":
        wtext = "🏆  VICTORY!  🎉"
        wcol  = C_PLAYER
    elif game.winner == "ai":
        wtext = "🤖  AI TRIUMPHED!  💀"
        wcol  = C_AI
    else:
        wtext = "🤝  STALEMATE!  ⚖️"
        wcol  = C_GOLD

    draw_text_glow(surf, wtext, f_big, wcol, w//2, h//2-110, glow_color=wcol, glow_r=3)

    sc = f_med.render(f"Player  {game.player_score}  —  {game.ai_score}  AI", True, C_TEXT)
    surf.blit(sc, sc.get_rect(center=(w//2, h//2-55)))

    play_btn.draw(surf)
    menu_btn.draw(surf)


def draw_game_screen(surf, game, restart_btn, menu_btn):
    w, h = surf.get_size()

    # ── Top bar ─────────────────────────────────────────
    bar = pygame.Surface((w, 64), pygame.SRCALPHA)
    bar.fill((15, 20, 40, 200))
    surf.blit(bar, (0, 0))

    f_score = get_font(26, bold=True)
    f_turn  = get_font(20, bold=True)
    f_label = get_font(13)

    # Player score
    pl = f_score.render(str(game.player_score), True, C_PLAYER)
    surf.blit(pl, pl.get_rect(centerx=w//4, centery=28))
    pl2 = f_label.render("PLAYER", True, C_DIM)
    surf.blit(pl2, pl2.get_rect(centerx=w//4, centery=48))

    # Turn label
    tl = game.turn_label
    tc = C_PLAYER if "PLAYER" in tl else (C_AI if "AI" in tl else C_GOLD)
    t = f_turn.render(tl, True, tc)
    surf.blit(t, t.get_rect(center=(w//2, 32)))

    # AI score
    ai_s = f_score.render(str(game.ai_score), True, C_AI)
    surf.blit(ai_s, ai_s.get_rect(centerx=3*w//4, centery=28))
    ai2 = f_label.render("AI", True, C_DIM)
    surf.blit(ai2, ai2.get_rect(centerx=3*w//4, centery=48))

    # ── Circular board decorations ──────────────────────
    ring_cx = w//2
    ring_cy = h//2 - 20
    r1 = int(min(w, h)*0.22)
    r2 = int(min(w, h)*0.38)
    s_board = pygame.Surface((w, h), pygame.SRCALPHA)
    
    # Outer Glow Ring
    pygame.draw.circle(s_board, (100, 150, 255, 15), (ring_cx, ring_cy), r2 + 60, width=40)
    
    # Tracks for pawns
    # Track 1
    pygame.draw.circle(s_board, (255, 255, 255, 20), (ring_cx, ring_cy), r1, width=2)
    pygame.draw.circle(s_board, (80, 100, 200, 10), (ring_cx, ring_cy), r1, width=12)
    # Track 2
    pygame.draw.circle(s_board, (255, 255, 255, 20), (ring_cx, ring_cy), r2, width=2)
    pygame.draw.circle(s_board, (80, 100, 200, 10), (ring_cx, ring_cy), r2, width=12)
    
    # Connecting Lines (spider-web look)
    for i in range(12):
        ang = math.radians(-90 + i * (360/12))
        p1 = (ring_cx + r1*math.cos(ang), ring_cy + r1*math.sin(ang))
        p2 = (ring_cx + r2*math.cos(ang + math.radians(15)), ring_cy + r2*math.sin(ang + math.radians(15)))
        pygame.draw.line(s_board, (100, 150, 255, 15), p1, p2, width=1)

    surf.blit(s_board, (0, 0))

    # ── Tiles ────────────────────────────────────────────
    for tile in game.tiles:
        draw_tile(surf, tile)

    # ── Bottom buttons ───────────────────────────────────
    restart_btn.draw(surf)
    menu_btn.draw(surf)
