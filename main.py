import pygame
import sys
import math
import ctypes
import time
from datetime import datetime

# Enable High DPI awareness
try: ctypes.windll.shcore.SetProcessDpiAwareness(1)
except:
    try: ctypes.windll.user32.SetProcessDPIAware()
    except: pass

from game import Game, STATE_GAME_OVER
from db_manager import DBManager
from ui import (
    SCREEN_NAME_INPUT, SCREEN_MENU, SCREEN_GAME, SCREEN_RULES, SCREEN_SETTINGS, 
    SCREEN_GAMEOVER, SCREEN_PAUSE, SCREEN_SAVE, SCREEN_LOAD, SCREEN_HISTORY, 
    SCREEN_EXIT_CONFIRM,
    ParticleSystem, Button, Slider, get_font,
    draw_gradient_bg, draw_name_input, draw_menu, draw_rules, draw_settings,
    draw_game_screen, draw_gameover, draw_pause_menu, draw_save_game,
    draw_saved_games, draw_game_history, draw_confirm_exit,
    C_PLAYER, C_AI, C_GOLD, C_DIM, C_WHITE, C_SUCCESS, C_DANGER
)
from audio import SoundManager

# ── Configuration ──────────────────────────────────────────
W, H = 550, 850
FPS  = 60
TITLE = "Color Memory Chess - Pro Edition 🏆"

class App:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption(TITLE)
        self.screen = pygame.display.set_mode((W, H))
        self.clock = pygame.time.Clock()
        self.running = True
        self.particles = ParticleSystem(W, H)
        self.fade = FadeTransition()
        self.audio = SoundManager()
        self.db = DBManager()
        self.screen_id = SCREEN_MENU
        self.next_screen = None
        self.game = Game(W, H)
        self.ai_mode = "ALPHA-BETA" # Default
        self.title_t = 0.0
        self.player_name = "Player 1"
        self.save_name = "Pro Game 1"
        self.sound_vol = 0.7
        self.music_vol = 0.5
        self._build_ui()
        self.fade.start()

    def _build_ui(self):
        f = get_font(32, bold=True)
        f_sm = get_font(22, bold=True)
        self.start_confirm_btn = Button(W//2, H//2 + 100, 260, 65, "START GAME", C_SUCCESS, f, "🚀")
        bw, bh = 320, 65
        self.menu_btns = [
            Button(W//2, H//2 - 40,  bw, bh, "START DUEL", C_PLAYER, f, "⚔️"),
            Button(W//2, H//2 + 35,  bw, bh, "RESUME", C_SUCCESS, f, "⏯️"),
            Button(W//2, H//2 + 110, bw, bh, "SAVED GAMES", (100, 50, 180), f, "💾"),
            Button(W//2, H//2 + 185, bw, bh, "HISTORY", (140, 100, 50), f, "📜"),
            Button(W//2, H//2 + 260, bw, bh, "SETTINGS", (80, 80, 120), f, "⚙️"),
            Button(W//2, H//2 + 335, bw, bh, "EXIT", C_DANGER, f, "❌")
        ]
        self.pause_btn = Button(W//2 - 90, H - 45, 160, 50, "PAUSE", (60, 60, 100), f_sm, "⏸️")
        self.hint_btn = Button(W//2 + 90, H - 45, 160, 50, "HINT", C_GOLD, f_sm, "💡")
        pbw = 240
        self.pause_btns = [
            Button(W//2, H//2 - 60, pbw, 55, "RESUME", C_SUCCESS, f_sm, "▶️"),
            Button(W//2, H//2, pbw, 55, "RESTART", (60, 120, 200), f_sm, "🔄"),
            Button(W//2, H//2 + 60, pbw, 55, "SAVE GAME", (120, 60, 180), f_sm, "💾"),
            Button(W//2, H//2 + 120, pbw, 55, "MAIN MENU", (80, 80, 140), f_sm, "🏠"),
            Button(W//2, H//2 + 180, pbw, 55, "EXIT GAME", C_DANGER, f_sm, "❌")
        ]
        self.pause_sliders = [
            Slider(W//2, H//2 - 160, 300, "Music", self.music_vol),
            Slider(W//2, H//2 - 220, 300, "Sound", self.sound_vol)
        ]
        self.back_btn = Button(W//2, H - 100, 200, 55, "BACK", (80, 80, 120), f_sm, "⬅️")
        self.save_confirm_btn = Button(W//2, H//2 + 40, 240, 55, "CONFIRM SAVE", C_SUCCESS, f_sm, "💾")
        self.ai_mode = "MEDIUM" # Default difficulty
        # ...
        self.ai_btns = [
            Button(W//2 - 150, H//2 + 140, 140, 45, "EASY", (60, 160, 100), f_sm),
            Button(W//2, H//2 + 140, 140, 45, "MEDIUM", (160, 140, 60), f_sm),
            Button(W//2 + 150, H//2 + 140, 140, 45, "HARD", (160, 60, 80), f_sm)
        ]
        self.play_again_btn = Button(W//2 - 110, H//2 + 130, 210, 55, "PLAY AGAIN", C_PLAYER, f_sm, "🎮")
        self.view_hist_btn = Button(W//2 + 110, H//2 + 130, 210, 55, "HISTORY", C_GOLD, f_sm, "📜")
        self.go_menu_btn = Button(W//2, H//2 + 200, 230, 55, "MAIN MENU", (80, 80, 140), f_sm, "🏠")
        self.exit_yes_btn = Button(W//2 - 100, H//2 + 60, 160, 55, "YES, EXIT", C_DANGER, f_sm, "🚪")
        self.exit_no_btn = Button(W//2 + 100, H//2 + 60, 160, 55, "CANCEL", (100, 100, 100), f_sm, "✖️")

    def go_to(self, screen_id):
        self.next_screen = screen_id
        self._fading_out = True; self._fade_alpha = 0; self.audio.play("click")

    def _handle_click(self, mx, my):
        s = self.screen_id
        if s == SCREEN_NAME_INPUT:
            if self.start_confirm_btn.on_click(mx, my) and self.player_name.strip(): self._start_game()
        elif s == SCREEN_MENU:
            if self.menu_btns[0].on_click(mx, my): self.go_to(SCREEN_NAME_INPUT)
            if self.menu_btns[1].on_click(mx, my):
                saves = self.db.get_saved_games()
                if saves: self._load_game(saves[0]["_id"])
                else: self.go_to(SCREEN_NAME_INPUT)
            if self.menu_btns[2].on_click(mx, my): self.go_to(SCREEN_LOAD)
            if self.menu_btns[3].on_click(mx, my): self.go_to(SCREEN_HISTORY)
            if self.menu_btns[4].on_click(mx, my): self.go_to(SCREEN_SETTINGS)
            if self.menu_btns[5].on_click(mx, my): self.go_to(SCREEN_EXIT_CONFIRM)
        elif s == SCREEN_GAME:
            if self.pause_btn.on_click(mx, my): self.screen_id = SCREEN_PAUSE; self.audio.play("click")
            self.game.handle_click(mx, my)
        elif s == SCREEN_PAUSE:
            if self.pause_btns[0].on_click(mx, my): self.screen_id = SCREEN_GAME; self.audio.play("click")
            if self.pause_btns[1].on_click(mx, my): self._start_game()
            if self.pause_btns[2].on_click(mx, my): self.screen_id = SCREEN_SAVE; self.audio.play("click")
            if self.pause_btns[3].on_click(mx, my): self.go_to(SCREEN_MENU)
            if self.pause_btns[4].on_click(mx, my): self.go_to(SCREEN_EXIT_CONFIRM)
        elif s == SCREEN_SAVE:
            if self.save_confirm_btn.on_click(mx, my):
                self.db.save_game(self.save_name, self.game.serialize(), self.game.state, 
                                  {"player": self.game.player_score, "ai": self.game.ai_score}, 
                                  self.game.ai_memory, self.player_name)
                self.screen_id = SCREEN_PAUSE; self.audio.play("click")
            if self.back_btn.on_click(mx, my): self.screen_id = SCREEN_PAUSE; self.audio.play("click")
        elif s == SCREEN_LOAD:
            if hasattr(self, 'load_btns'):
                for save_id, (l_btn, d_btn) in self.load_btns.items():
                    if l_btn.on_click(mx, my): self._load_game(save_id)
                    if d_btn.on_click(mx, my): self.db.delete_save(save_id); self.go_to(SCREEN_LOAD)
            if self.back_btn.on_click(mx, my): self.go_to(SCREEN_MENU)
        elif s == SCREEN_HISTORY or s == SCREEN_RULES:
            if self.back_btn.on_click(mx, my): self.go_to(SCREEN_MENU)
        elif s == SCREEN_SETTINGS:
            if self.ai_btns[0].on_click(mx, my): self.ai_mode = "EASY"; self.audio.play("click")
            if self.ai_btns[1].on_click(mx, my): self.ai_mode = "MEDIUM"; self.audio.play("click")
            if self.ai_btns[2].on_click(mx, my): self.ai_mode = "HARD"; self.audio.play("click")
            if self.back_btn.on_click(mx, my): self.go_to(SCREEN_MENU)
        elif s == SCREEN_GAMEOVER:
            if self.play_again_btn.on_click(mx, my): self._start_game()
            if self.view_hist_btn.on_click(mx, my): self.go_to(SCREEN_HISTORY)
            if self.go_menu_btn.on_click(mx, my): self.go_to(SCREEN_MENU)
        elif s == SCREEN_EXIT_CONFIRM:
            if self.exit_yes_btn.on_click(mx, my): self.running = False
            if self.exit_no_btn.on_click(mx, my): self.screen_id = SCREEN_MENU if not self.game.tiles else SCREEN_PAUSE; self.audio.play("click")

    def _start_game(self):
        self.game = Game(W, H); self.game.player_name = self.player_name; self.game.ai_engine.difficulty = self.ai_mode; self.go_to(SCREEN_GAME)

    def _load_game(self, save_id):
        save = self.db.load_game(save_id)
        if save:
            self.game = Game(W, H); self.game.deserialize(save["board"])
            self.player_name = save.get("player", self.player_name); self.game.player_name = self.player_name; self.go_to(SCREEN_GAME)

    def update(self, dt):
        self.title_t += dt; self.particles.update(); self.fade.update(dt)
        if hasattr(self, '_fading_out') and self._fading_out:
            self._fade_alpha += 600 * dt
            if self._fade_alpha >= 255:
                self._fading_out = False; self.screen_id = self.next_screen; self.fade.start()
                if self.screen_id == SCREEN_LOAD:
                    self.load_btns = {}
                    saves = self.db.get_saved_games()
                    for i, s in enumerate(saves[:5]):
                        l_btn = Button(W//2 - 60, H//2 - 100 + i*70, 280, 50, f"{s['name']}", (100, 60, 180), get_font(18))
                        d_btn = Button(W//2 + 160, H//2 - 100 + i*70, 60, 50, "DEL", C_DANGER, get_font(14))
                        self.load_btns[s["_id"]] = (l_btn, d_btn)
        mx, my = pygame.mouse.get_pos(); clicked = pygame.mouse.get_pressed()[0]
        if self.screen_id == SCREEN_NAME_INPUT: self.start_confirm_btn.update(mx, my, dt)
        elif self.screen_id == SCREEN_MENU:
            for b in self.menu_btns: b.update(mx, my, dt)
        elif self.screen_id == SCREEN_GAME:
            old_s_p, old_s_ai = self.game.player_score, self.game.ai_score; self.game.update(dt)
            if self.game.sound_trigger: self.audio.play(self.game.sound_trigger); self.game.sound_trigger = None
            if self.game.player_score > old_s_p or self.game.ai_score > old_s_ai: self.audio.play("match")
            self.pause_btn.update(mx, my, dt); self.hint_btn.update(mx, my, dt)
            if self.game.state == "game_over":
                if not hasattr(self, '_go_trig'): self._go_trig = True; self._go_timer = 2.0; self.audio.play("win")
                self._go_timer -= dt
                if self._go_timer <= 0:
                    self.db.add_to_history(self.game.winner, self.game.player_score, self.game.ai_score, self.game.total_moves, self.game.total_time, self.player_name)
                    del self._go_trig; self.go_to(SCREEN_GAMEOVER)
        elif self.screen_id == SCREEN_PAUSE:
            for b in self.pause_btns: b.update(mx, my, dt)
            for s in self.pause_sliders:
                s.update(mx, my, clicked)
                if s.label == "Music": self.music_vol = s.value
                else: self.sound_vol = s.value; self.audio.set_volume(s.value)
        elif self.screen_id == SCREEN_SAVE: self.save_confirm_btn.update(mx, my, dt); self.back_btn.update(mx, my, dt)
        elif self.screen_id == SCREEN_LOAD:
            if hasattr(self, 'load_btns'):
                for l_b, d_b in self.load_btns.values(): l_b.update(mx, my, dt); d_b.update(mx, my, dt)
            self.back_btn.update(mx, my, dt)
        elif self.screen_id == SCREEN_SETTINGS:
            for b in self.ai_btns: b.update(mx, my, dt)
            self.back_btn.update(mx, my, dt)
        elif self.screen_id == SCREEN_GAMEOVER: self.play_again_btn.update(mx, my, dt); self.view_hist_btn.update(mx, my, dt); self.go_menu_btn.update(mx, my, dt)
        elif self.screen_id == SCREEN_EXIT_CONFIRM: self.exit_yes_btn.update(mx, my, dt); self.exit_no_btn.update(mx, my, dt)

    def draw(self):
        draw_gradient_bg(self.screen); self.particles.draw(self.screen)
        s = self.screen_id
        if s == SCREEN_NAME_INPUT: draw_name_input(self.screen, [self.start_confirm_btn], self.player_name)
        elif s == SCREEN_MENU: draw_menu(self.screen, self.menu_btns, self.title_t)
        elif s == SCREEN_GAME: draw_game_screen(self.screen, self.game, [self.pause_btn, self.hint_btn])
        elif s == SCREEN_PAUSE: draw_pause_menu(self.screen, self.pause_btns, self.pause_sliders)
        elif s == SCREEN_SAVE: draw_save_game(self.screen, [self.save_confirm_btn, self.back_btn], self.save_name)
        elif s == SCREEN_LOAD:
            draw_saved_games(self.screen, [self.back_btn], self.db.get_saved_games())
            if hasattr(self, 'load_btns'):
                for l_b, d_b in self.load_btns.values(): l_b.draw(self.screen); d_b.draw(self.screen)
        elif s == SCREEN_HISTORY: draw_game_history(self.screen, [self.back_btn], self.db.get_game_history())
        elif s == SCREEN_SETTINGS:
            draw_settings(self.screen, self.ai_btns, [], self.ai_mode)
        elif s == SCREEN_GAMEOVER: draw_gameover(self.screen, self.game, [self.play_again_btn, self.view_hist_btn, self.go_menu_btn])
        elif s == SCREEN_EXIT_CONFIRM: draw_confirm_exit(self.screen, [self.exit_yes_btn, self.exit_no_btn])
        self.fade.draw(self.screen)
        if hasattr(self, '_fading_out') and self._fading_out:
            ov = pygame.Surface((W, H)); ov.fill((0, 0, 0)); ov.set_alpha(int(self._fade_alpha)); self.screen.blit(ov, (0, 0))
        pygame.display.flip()

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT: self.running = False
                if event.type == pygame.KEYDOWN:
                    if self.screen_id == SCREEN_NAME_INPUT:
                        if event.key == pygame.K_BACKSPACE: self.player_name = self.player_name[:-1]
                        elif len(self.player_name) < 15: self.player_name += event.unicode
                    elif self.screen_id == SCREEN_SAVE:
                        if event.key == pygame.K_BACKSPACE: self.save_name = self.save_name[:-1]
                        elif len(self.save_name) < 20: self.save_name += event.unicode
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1: self._handle_click(*event.pos)
            self.update(dt); self.draw()
        pygame.quit(); sys.exit()

class FadeTransition:
    def __init__(self, speed=400): self.alpha = 255; self.speed = speed; self.fading = False
    def start(self): self.alpha = 255; self.fading = True
    def update(self, dt):
        if self.fading:
            self.alpha -= self.speed * dt
            if self.alpha <= 0: self.alpha = 0; self.fading = False
    def draw(self, surf):
        if self.alpha > 0:
            s = pygame.Surface(surf.get_size()); s.fill((0, 0, 0)); s.set_alpha(int(self.alpha)); surf.blit(s, (0, 0))

if __name__ == "__main__": App().run()
