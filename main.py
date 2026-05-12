"""
main.py - Entry point for Color Memory Chess
Run: python main.py
"""

import pygame
import sys
import math

from game import Game, STATE_GAME_OVER, STATE_PLAYER_TURN, STATE_AI_THINKING, STATE_FLIP_BACK
from ui import (
    SCREEN_MENU, SCREEN_GAME, SCREEN_RULES, SCREEN_SETTINGS, SCREEN_GAMEOVER,
    ParticleSystem, Button, get_font,
    draw_gradient_bg, draw_menu, draw_rules, draw_settings,
    draw_game_screen, draw_gameover,
    C_PLAYER, C_AI, C_GOLD, C_DIM, C_WHITE,
)

# ── Window ────────────────────────────────────────────────
W, H = 800, 700
FPS  = 60
TITLE = "Color Memory Chess"


# ═══════════════════════════════════════════════════════════
# Fade transition helper
# ═══════════════════════════════════════════════════════════
class FadeTransition:
    def __init__(self):
        self.alpha    = 0
        self.fading   = False   # True = fading in (alpha 0→255), False = fading out
        self.done     = False
        self.speed    = 400     # alpha units per second

    def start_fade_in(self):
        self.alpha  = 255
        self.fading = True
        self.done   = False

    def update(self, dt):
        if not self.fading:
            return
        self.alpha -= self.speed * dt
        if self.alpha <= 0:
            self.alpha  = 0
            self.fading = False
            self.done   = True

    def draw(self, surf):
        if self.alpha > 0:
            s = pygame.Surface(surf.get_size())
            s.fill((0, 0, 0))
            s.set_alpha(int(self.alpha))
            surf.blit(s, (0, 0))


# ═══════════════════════════════════════════════════════════
# Main App
# ═══════════════════════════════════════════════════════════
class App:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption(TITLE)
        self.screen  = pygame.display.set_mode((W, H))
        self.clock   = pygame.time.Clock()
        self.running = True

        self.particles = ParticleSystem(W, H, count=70)
        self.fade      = FadeTransition()
        self.screen_id = SCREEN_MENU
        self.next_screen = None   # set when fade-out is triggered

        self.game      = Game(W, H)
        self.ai_smart  = True
        self.title_t   = 0.0

        self._build_buttons()
        self.fade.start_fade_in()

    # ── Button factory ────────────────────────────────────
    def _build_buttons(self):
        f     = get_font(20, bold=True)
        f_sm  = get_font(18, bold=True)

        # ── Menu ──
        bw, bh = 240, 54
        self.menu_btns = [
            Button(W//2, H*2//3 - 10,      bw, bh, "🎮  PLAY NOW",  C_PLAYER, f),
            Button(W//2, H*2//3 + 70,      bw, bh, "📜  GAME RULES", (60,140,90), f),
            Button(W//2, H*2//3 + 140,     bw, bh, "⚙️  PREFERENCES", (120,60,180), f),
            Button(W//2, H*2//3 + 210,     bw, bh, "❌  QUIT GAME", (160,40,60), f),
        ]

        # ── Game screen ──
        self.restart_btn = Button(W//2 - 90, H - 38, 160, 48, "🔄 Restart", (60,120,200), f_sm)
        self.gmenu_btn   = Button(W//2 + 90, H - 38, 160, 48, "🏠 Main Menu", (80,60,140),  f_sm)

        # ── Rules / Settings ──
        self.back_btn    = Button(W//2, H - 55, 180, 48, "⬅️ Back", (70,70,120), f_sm)
        self.toggle_btn  = Button(W//2, H//2 + 30, 220, 48, "🔄 Switch AI Mode", (100,60,180), f_sm)

        # ── Game over ──
        self.play_again_btn = Button(W//2 - 100, H//2 + 80, 180, 50, "🎮 Play Again", C_PLAYER, f_sm)
        self.go_menu_btn    = Button(W//2 + 100, H//2 + 80, 180, 50, "🏠 Exit to Menu", (80,60,140), f_sm)

    # ── Screen transition ─────────────────────────────────
    def go_to(self, screen_id):
        """Trigger fade-out then switch screen."""
        self.next_screen = screen_id
        self.fade.alpha  = 0
        self.fade.fading = False
        self._fading_out = True
        self._fade_out_alpha = 0.0

    # ── Event handling ────────────────────────────────────
    def handle_events(self):
        mx, my = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._handle_click(mx, my)

    def _handle_click(self, mx, my):
        s = self.screen_id

        if s == SCREEN_MENU:
            if self.menu_btns[0].on_click(mx, my): self._start_game()
            if self.menu_btns[1].on_click(mx, my): self.go_to(SCREEN_RULES)
            if self.menu_btns[2].on_click(mx, my): self.go_to(SCREEN_SETTINGS)
            if self.menu_btns[3].on_click(mx, my): self.running = False

        elif s == SCREEN_GAME:
            if self.restart_btn.on_click(mx, my): self._start_game()
            if self.gmenu_btn.on_click(mx, my):   self.go_to(SCREEN_MENU)
            self.game.handle_click(mx, my)

        elif s == SCREEN_RULES:
            if self.back_btn.on_click(mx, my): self.go_to(SCREEN_MENU)

        elif s == SCREEN_SETTINGS:
            if self.toggle_btn.on_click(mx, my): self.ai_smart = not self.ai_smart
            if self.back_btn.on_click(mx, my):   self.go_to(SCREEN_MENU)

        elif s == SCREEN_GAMEOVER:
            if self.play_again_btn.on_click(mx, my): self._start_game()
            if self.go_menu_btn.on_click(mx, my):    self.go_to(SCREEN_MENU)

    def _start_game(self):
        self.game = Game(W, H)
        self.go_to(SCREEN_GAME)

    # ── Update ────────────────────────────────────────────
    def update(self, dt):
        self.title_t += dt
        self.particles.update()
        self.fade.update(dt)

        # Fade-out logic (we blend alpha up then switch screen)
        if hasattr(self, '_fading_out') and self._fading_out:
            self._fade_out_alpha += 500 * dt
            self.fade.alpha = min(255, int(self._fade_out_alpha))
            if self._fade_out_alpha >= 255:
                self._fading_out = False
                self.screen_id   = self.next_screen
                self.next_screen = None
                self.fade.start_fade_in()
                self._rebuild_if_needed()

        mx, my = pygame.mouse.get_pos()
        dt_f = dt

        if self.screen_id == SCREEN_MENU:
            for btn in self.menu_btns:
                btn.update(mx, my, dt_f)

        elif self.screen_id == SCREEN_GAME:
            self.game.update(dt)
            self.restart_btn.update(mx, my, dt_f)
            self.gmenu_btn.update(mx, my, dt_f)
            # Auto-transition to game over
            if self.game.state == STATE_GAME_OVER and self.screen_id == SCREEN_GAME:
                if not hasattr(self, '_go_triggered'):
                    self._go_triggered = True
                    # Small delay then show gameover screen
                    self._go_timer = 1.8
            if hasattr(self, '_go_triggered') and self._go_triggered:
                self._go_timer -= dt
                if self._go_timer <= 0:
                    self._go_triggered = False
                    self.go_to(SCREEN_GAMEOVER)

        elif self.screen_id == SCREEN_RULES:
            self.back_btn.update(mx, my, dt_f)

        elif self.screen_id == SCREEN_SETTINGS:
            self.toggle_btn.update(mx, my, dt_f)
            self.back_btn.update(mx, my, dt_f)

        elif self.screen_id == SCREEN_GAMEOVER:
            self.play_again_btn.update(mx, my, dt_f)
            self.go_menu_btn.update(mx, my, dt_f)

    def _rebuild_if_needed(self):
        # Reset gameover auto-transition flag
        if hasattr(self, '_go_triggered'):
            self._go_triggered = False

    # ── Draw ──────────────────────────────────────────────
    def draw(self):
        surf = self.screen
        draw_gradient_bg(surf)
        self.particles.draw(surf)

        s = self.screen_id
        if s == SCREEN_MENU:
            draw_menu(surf, self.menu_btns, self.title_t)
        elif s == SCREEN_GAME:
            draw_game_screen(surf, self.game, self.restart_btn, self.gmenu_btn)
        elif s == SCREEN_RULES:
            draw_rules(surf, self.back_btn)
        elif s == SCREEN_SETTINGS:
            draw_settings(surf, self.toggle_btn, self.back_btn, self.ai_smart)
        elif s == SCREEN_GAMEOVER:
            draw_game_screen(surf, self.game, self.restart_btn, self.gmenu_btn)
            draw_gameover(surf, self.game, self.play_again_btn, self.go_menu_btn)

        self.fade.draw(surf)
        pygame.display.flip()

    # ── Main loop ─────────────────────────────────────────
    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            self.handle_events()
            self.update(dt)
            self.draw()
        pygame.quit()
        sys.exit()


# ═══════════════════════════════════════════════════════════
if __name__ == "__main__":
    App().run()
