import pygame
import random
import sys

# ─── Constants ────────────────────────────────────────────────────────────────

WINDOW_W, WINDOW_H = 640, 680   # extra 40 px at top for HUD
GRID_SIZE          = 20          # px per cell
COLS               = WINDOW_W  // GRID_SIZE   # 32
ROWS               = (WINDOW_H - 40) // GRID_SIZE  # 32

# Colour palette
BG_DARK    = (15,  17,  26)
BG_GRID    = (20,  23,  35)
SNAKE_HEAD = (80,  200, 120)
SNAKE_BODY = (46,  139,  87)
SNAKE_OUTLINE = (30, 90, 55)
FOOD_COLOR = (255, 80,  80)
FOOD_SHINE = (255, 160, 160)
HUD_BG     = (10,  12,  20)
TEXT_COLOR = (200, 220, 200)
ACCENT     = (80,  200, 120)
BTN_NORMAL = (30,  34,  50)
BTN_HOVER  = (50,  54,  80)
BTN_BORDER = (80,  200, 120)
OVERLAY_BG = (0,   0,   0,  170)

# Directions
UP    = ( 0, -1)
DOWN  = ( 0,  1)
LEFT  = (-1,  0)
RIGHT = ( 1,  0)

# Speed presets  (label, FPS)
SPEED_PRESETS = [
    ("Slow",   6),
    ("Normal", 10),
    ("Fast",   16),
    ("Turbo",  32),
]


# ─── Helpers ──────────────────────────────────────────────────────────────────

def grid_rect(col, row):
    """Return pygame.Rect for a grid cell (offset by 40 px HUD)."""
    return pygame.Rect(col * GRID_SIZE, 40 + row * GRID_SIZE, GRID_SIZE, GRID_SIZE)


def draw_rounded_rect(surf, color, rect, radius=6, border=0, border_color=None):
    pygame.draw.rect(surf, color, rect, border_radius=radius)
    if border and border_color:
        pygame.draw.rect(surf, border_color, rect, border, border_radius=radius)


def draw_grid(surf):
    for c in range(COLS):
        for r in range(ROWS):
            rect = grid_rect(c, r)
            pygame.draw.rect(surf, BG_GRID, rect, 1)


# ─── Button ───────────────────────────────────────────────────────────────────

class Button:
    def __init__(self, rect, label, font):
        self.rect   = pygame.Rect(rect)
        self.label  = label
        self.font   = font
        self.hovered = False

    def draw(self, surf):
        color = BTN_HOVER if self.hovered else BTN_NORMAL
        draw_rounded_rect(surf, color, self.rect, radius=8,
                          border=2, border_color=BTN_BORDER)
        txt = self.font.render(self.label, True, TEXT_COLOR)
        surf.blit(txt, txt.get_rect(center=self.rect.center))

    def update(self, mouse_pos):
        self.hovered = self.rect.collidepoint(mouse_pos)

    def is_clicked(self, event):
        return (event.type == pygame.MOUSEBUTTONDOWN and
                event.button == 1 and
                self.rect.collidepoint(event.pos))


# ─── Game ─────────────────────────────────────────────────────────────────────

class SnakeGame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
        pygame.display.set_caption("iSnake")
        self.clock  = pygame.time.Clock()

        self.font_big   = pygame.font.SysFont("consolas", 42, bold=True)
        self.font_mid   = pygame.font.SysFont("consolas", 24, bold=True)
        self.font_small = pygame.font.SysFont("consolas", 16)

        self.speed_index = 1          # default: Normal
        self.fps          = SPEED_PRESETS[self.speed_index][1]

        self._build_menu_buttons()
        self.state = "menu"           # "menu" | "playing" | "paused" | "dead"

    # ── button helpers ────────────────────────────────────────────────────────

    def _build_menu_buttons(self):
        cx = WINDOW_W // 2
        self.btn_play   = Button((cx - 100, 290, 200, 48), "▶  Play",  self.font_mid)
        self.btn_quit_m = Button((cx - 100, 360, 200, 48), "✕  Quit",  self.font_mid)

        # speed selector buttons  ← / →
        self.btn_spd_l  = Button((cx - 130, 220, 44, 40), "◀", self.font_mid)
        self.btn_spd_r  = Button((cx +  86, 220, 44, 40), "▶", self.font_mid)

        # in-game overlay buttons
        self.btn_resume = Button((cx - 100, 320, 200, 48), "▶  Resume", self.font_mid)
        self.btn_menu   = Button((cx - 100, 388, 200, 48), "⌂  Menu",   self.font_mid)
        self.btn_retry  = Button((cx - 100, 320, 200, 48), "↺  Retry",  self.font_mid)
        self.btn_menu2  = Button((cx - 100, 388, 200, 48), "⌂  Menu",   self.font_mid)

    # ── reset / init game state ───────────────────────────────────────────────

    def _reset(self):
        mid_c, mid_r = COLS // 2, ROWS // 2
        self.snake     = [(mid_c, mid_r), (mid_c - 1, mid_r), (mid_c - 2, mid_r)]
        self.direction = RIGHT
        self.next_dir  = RIGHT
        self.score     = 0
        self.high_score = getattr(self, "high_score", 0)
        self._spawn_food()
        self.grow_pending = 0

    def _spawn_food(self):
        occupied = set(self.snake)
        while True:
            pos = (random.randint(0, COLS - 1), random.randint(0, ROWS - 1))
            if pos not in occupied:
                self.food = pos
                break

    # ── main loop ─────────────────────────────────────────────────────────────

    def run(self):
        while True:
            if   self.state == "menu":    self._loop_menu()
            elif self.state == "playing": self._loop_playing()
            elif self.state == "paused":  self._loop_paused()
            elif self.state == "dead":    self._loop_dead()

    # ── MENU ──────────────────────────────────────────────────────────────────

    def _loop_menu(self):
        while self.state == "menu":
            mx, my = pygame.mouse.get_pos()
            for btn in (self.btn_play, self.btn_quit_m,
                        self.btn_spd_l, self.btn_spd_r):
                btn.update((mx, my))

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._quit()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                    self._start_game()
                if self.btn_play.is_clicked(event):
                    self._start_game()
                if self.btn_quit_m.is_clicked(event):
                    self._quit()
                if self.btn_spd_l.is_clicked(event):
                    self.speed_index = (self.speed_index - 1) % len(SPEED_PRESETS)
                    self.fps = SPEED_PRESETS[self.speed_index][1]
                if self.btn_spd_r.is_clicked(event):
                    self.speed_index = (self.speed_index + 1) % len(SPEED_PRESETS)
                    self.fps = SPEED_PRESETS[self.speed_index][1]

            self._draw_menu()
            self.clock.tick(60)

    def _start_game(self):
        self._reset()
        self.state = "playing"

    def _draw_menu(self):
        s = self.screen
        s.fill(BG_DARK)
        draw_grid(s)

        # Title
        title = self.font_big.render("🐍  iSNAKE", True, ACCENT)
        s.blit(title, title.get_rect(center=(WINDOW_W // 2, 120)))

        sub = self.font_small.render("Use arrow keys or WASD to move • P to pause", True, (120, 140, 120))
        s.blit(sub, sub.get_rect(center=(WINDOW_W // 2, 170)))

        # Speed selector
        cx = WINDOW_W // 2
        lbl = self.font_small.render("SPEED", True, (120, 140, 120))
        s.blit(lbl, lbl.get_rect(center=(cx, 206)))

        spd_lbl = self.font_mid.render(SPEED_PRESETS[self.speed_index][0], True, ACCENT)
        s.blit(spd_lbl, spd_lbl.get_rect(center=(cx, 240)))

        self.btn_spd_l.draw(s)
        self.btn_spd_r.draw(s)
        self.btn_play.draw(s)
        self.btn_quit_m.draw(s)

        # High-score
        hs = getattr(self, "high_score", 0)
        hs_txt = self.font_small.render(f"Best: {hs}", True, (120, 160, 120))
        s.blit(hs_txt, hs_txt.get_rect(center=(WINDOW_W // 2, 430)))

        pygame.display.flip()

    # ── PLAYING ───────────────────────────────────────────────────────────────

    def _loop_playing(self):
        while self.state == "playing":
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._quit()
                if event.type == pygame.KEYDOWN:
                    self._handle_key(event.key)

            self._update()
            self._draw_game()
            self.clock.tick(self.fps)

    def _handle_key(self, key):
        dirs = {
            pygame.K_UP:    UP,    pygame.K_w: UP,
            pygame.K_DOWN:  DOWN,  pygame.K_s: DOWN,
            pygame.K_LEFT:  LEFT,  pygame.K_a: LEFT,
            pygame.K_RIGHT: RIGHT, pygame.K_d: RIGHT,
        }
        if key in dirs:
            nd = dirs[key]
            # prevent reversing
            if (nd[0] + self.direction[0], nd[1] + self.direction[1]) != (0, 0):
                self.next_dir = nd
        if key == pygame.K_p or key == pygame.K_ESCAPE:
            self.state = "paused"

    def _update(self):
        self.direction = self.next_dir
        head = self.snake[0]
        new_head = (head[0] + self.direction[0], head[1] + self.direction[1])

        # Wrap around walls instead of dying
        new_head = (new_head[0] % COLS, new_head[1] % ROWS)

        # Self collision
        if new_head in self.snake:
            self._die()
            return

        self.snake.insert(0, new_head)

        # Eat food
        if new_head == self.food:
            self.score += 1
            if self.score > self.high_score:
                self.high_score = self.score
            self._spawn_food()
        else:
            self.snake.pop()

    def _die(self):
        self.state = "dead"

    # ── DRAW GAME ─────────────────────────────────────────────────────────────

    def _draw_game(self):
        s = self.screen
        s.fill(BG_DARK)
        draw_grid(s)
        self._draw_hud()
        self._draw_food()
        self._draw_snake()
        pygame.display.flip()

    def _draw_hud(self):
        s = self.screen
        pygame.draw.rect(s, HUD_BG, (0, 0, WINDOW_W, 40))
        pygame.draw.line(s, ACCENT, (0, 40), (WINDOW_W, 40), 1)

        score_txt = self.font_mid.render(f"Score: {self.score}", True, ACCENT)
        s.blit(score_txt, (12, 8))

        hs_txt = self.font_small.render(f"Best: {self.high_score}", True, (120, 160, 120))
        s.blit(hs_txt, hs_txt.get_rect(midright=(WINDOW_W - 70, 20)))

        spd_txt = self.font_small.render(
            f"Speed: {SPEED_PRESETS[self.speed_index][0]}", True, (120, 140, 120))
        s.blit(spd_txt, spd_txt.get_rect(midright=(WINDOW_W - 12, 20)))

    def _draw_food(self):
        s = self.screen
        fc, fr = self.food
        rect = grid_rect(fc, fr).inflate(-4, -4)
        pygame.draw.ellipse(s, FOOD_COLOR, rect)
        # small shine
        shine = pygame.Rect(rect.x + 3, rect.y + 3, 5, 5)
        pygame.draw.ellipse(s, FOOD_SHINE, shine)

    def _draw_snake(self):
        s = self.screen
        for i, (sc, sr) in enumerate(self.snake):
            rect = grid_rect(sc, sr).inflate(-2, -2)
            color = SNAKE_HEAD if i == 0 else SNAKE_BODY
            draw_rounded_rect(s, color, rect, radius=5,
                              border=1, border_color=SNAKE_OUTLINE)
        # eyes on head
        if self.snake:
            hc, hr = self.snake[0]
            hr_rect = grid_rect(hc, hr)
            cx = hr_rect.centerx
            cy = hr_rect.centery
            d = self.direction
            eye_off = 4
            if d == RIGHT:
                e1 = (cx + 4, cy - 3)
                e2 = (cx + 4, cy + 3)
            elif d == LEFT:
                e1 = (cx - 4, cy - 3)
                e2 = (cx - 4, cy + 3)
            elif d == UP:
                e1 = (cx - 3, cy - 4)
                e2 = (cx + 3, cy - 4)
            else:
                e1 = (cx - 3, cy + 4)
                e2 = (cx + 3, cy + 4)
            pygame.draw.circle(s, (20, 20, 30), e1, 2)
            pygame.draw.circle(s, (20, 20, 30), e2, 2)

    # ── PAUSED ────────────────────────────────────────────────────────────────

    def _loop_paused(self):
        while self.state == "paused":
            mx, my = pygame.mouse.get_pos()
            for btn in (self.btn_resume, self.btn_menu):
                btn.update((mx, my))

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._quit()
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_p, pygame.K_ESCAPE):
                        self.state = "playing"
                if self.btn_resume.is_clicked(event):
                    self.state = "playing"
                if self.btn_menu.is_clicked(event):
                    self.state = "menu"

            # draw frozen game behind overlay
            self._draw_game()
            self._draw_overlay("PAUSED", "")
            self.btn_resume.draw(self.screen)
            self.btn_menu.draw(self.screen)
            pygame.display.flip()
            self.clock.tick(60)

    # ── DEAD ──────────────────────────────────────────────────────────────────

    def _loop_dead(self):
        while self.state == "dead":
            mx, my = pygame.mouse.get_pos()
            for btn in (self.btn_retry, self.btn_menu2):
                btn.update((mx, my))

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._quit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        self._start_game()
                    if event.key == pygame.K_m:
                        self.state = "menu"
                if self.btn_retry.is_clicked(event):
                    self._start_game()
                if self.btn_menu2.is_clicked(event):
                    self.state = "menu"

            self._draw_game()
            self._draw_overlay("GAME OVER", f"Score: {self.score}")
            self.btn_retry.draw(self.screen)
            self.btn_menu2.draw(self.screen)
            pygame.display.flip()
            self.clock.tick(60)

    # ── Overlay helper ────────────────────────────────────────────────────────

    def _draw_overlay(self, title, subtitle):
        s = self.screen
        overlay = pygame.Surface((WINDOW_W, WINDOW_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        s.blit(overlay, (0, 0))

        t = self.font_big.render(title, True, ACCENT)
        s.blit(t, t.get_rect(center=(WINDOW_W // 2, 240)))

        if subtitle:
            st = self.font_mid.render(subtitle, True, TEXT_COLOR)
            s.blit(st, st.get_rect(center=(WINDOW_W // 2, 290)))

        hint_map = {
            "PAUSED":    "P / ESC to resume",
            "GAME OVER": "R to retry  •  M for menu",
        }
        hint = self.font_small.render(hint_map.get(title, ""), True, (100, 120, 100))
        s.blit(hint, hint.get_rect(center=(WINDOW_W // 2, 450)))

    # ── Quit ──────────────────────────────────────────────────────────────────

    def _quit(self):
        pygame.quit()
        sys.exit()


# ─── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    SnakeGame().run()