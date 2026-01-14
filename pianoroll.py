import math
import random
import sys
import time
from dataclasses import dataclass

import pygame

SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 720
FPS = 60

BACKGROUND = (12, 12, 18)
LANE_COLOR = (32, 32, 46)
TARGET_LINE = (240, 240, 255)
NOTE_COLOR = (109, 226, 255)
NOTE_HIT = (126, 255, 153)
NOTE_MISS = (255, 109, 120)
TEXT_COLOR = (240, 240, 255)

ROWS = [
    ("QWERTYUIOP", "ЙЦУКЕНГШЩЗ", 0.0),
    ("ASDFGHJKL", "ФЫВАПРОЛД", 0.5),
    ("ZXCVBNM", "ЯЧСМИТЬ", 1.0),
]
ALL_LETTERS = "".join("".join((latin, cyrillic)) for latin, cyrillic, _ in ROWS)

LANE_TOP = 60
LANE_BOTTOM = SCREEN_HEIGHT - 140
TARGET_Y = LANE_BOTTOM - 10

KEY_SIZE = 44
KEY_GAP = 8

LEVEL_SETTINGS = [
    (0.65, 250.0),
    (0.6, 270.0),
    (0.55, 290.0),
    (0.5, 310.0),
    (0.45, 330.0),
    (0.4, 350.0),
    (0.36, 370.0),
    (0.32, 390.0),
    (0.28, 420.0),
    (0.24, 450.0),
]

WINDOWS = {
    "perfect": 14,
    "great": 26,
    "good": 40,
}

SCORES = {
    "perfect": 300,
    "great": 150,
    "good": 75,
}


@dataclass
class Note:
    letter: str
    x: float
    y: float
    hit: bool = False
    missed: bool = False


class PianoRoll:
    def __init__(self) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Пианорол")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 32)
        self.large_font = pygame.font.Font(None, 48)

        self.lanes, self.key_positions = self._build_lanes()
        self.notes: list[Note] = []
        self.last_spawn = time.time()

        self.level = 1
        self.spawn_interval, self.fall_speed = LEVEL_SETTINGS[self.level - 1]

        self.score = 0
        self.combo = 0
        self.max_combo = 0
        self.hits = 0
        self.misses = 0
        self.running = True
        self.start_time = time.time()

    def _build_lanes(self) -> tuple[dict[str, tuple[float, int]], list[tuple[pygame.Rect, str]]]:
        lanes: dict[str, tuple[float, int]] = {}
        keys: list[tuple[pygame.Rect, str]] = []
        max_keys = len(ROWS[0][0])
        row_width = max_keys * KEY_SIZE + (max_keys - 1) * KEY_GAP
        start_x = (SCREEN_WIDTH - row_width) / 2
        base_y = LANE_BOTTOM + 20
        for row_index, (latin_row, cyrillic_row, offset_units) in enumerate(ROWS):
            row_x = start_x + offset_units * (KEY_SIZE + KEY_GAP)
            row_y = base_y + row_index * (KEY_SIZE + KEY_GAP)
            for i, latin_letter in enumerate(latin_row):
                cyrillic_letter = cyrillic_row[i]
                x = row_x + i * (KEY_SIZE + KEY_GAP)
                rect = pygame.Rect(x, row_y, KEY_SIZE, KEY_SIZE)
                center_x = rect.centerx
                lanes[latin_letter] = (center_x, row_index)
                lanes[cyrillic_letter] = (center_x, row_index)
                keys.append((rect, f"{latin_letter}/{cyrillic_letter}"))
        return lanes, keys

    def spawn_note(self) -> None:
        letter = random.choice(ALL_LETTERS)
        x, _ = self.lanes[letter]
        self.notes.append(Note(letter=letter, x=x, y=LANE_TOP - 40))

    def set_level(self, level: int) -> None:
        level = max(1, min(10, level))
        self.level = level
        self.spawn_interval, self.fall_speed = LEVEL_SETTINGS[self.level - 1]

    def handle_hit(self, letter: str) -> None:
        candidates = [note for note in self.notes if note.letter == letter and not note.hit and not note.missed]
        if not candidates:
            self.register_miss()
            return
        note = min(candidates, key=lambda n: abs(n.y - TARGET_Y))
        distance = abs(note.y - TARGET_Y)
        for tier, window in WINDOWS.items():
            if distance <= window:
                note.hit = True
                self.register_hit(tier)
                return
        self.register_miss()

    def register_hit(self, tier: str) -> None:
        self.score += SCORES[tier]
        self.combo += 1
        self.max_combo = max(self.max_combo, self.combo)
        self.hits += 1

    def register_miss(self) -> None:
        self.combo = 0
        self.misses += 1

    def update_notes(self, dt: float) -> None:
        for note in self.notes:
            if note.hit or note.missed:
                continue
            note.y += self.fall_speed * dt
            if note.y > TARGET_Y + WINDOWS["good"]:
                note.missed = True
                self.register_miss()
        self.notes = [note for note in self.notes if note.y < SCREEN_HEIGHT + 60]

    def draw_lanes(self) -> None:
        for rect, label_text in self.key_positions:
            center_x = rect.centerx
            pygame.draw.line(self.screen, LANE_COLOR, (center_x, LANE_TOP), (center_x, LANE_BOTTOM), 3)
            pygame.draw.rect(self.screen, LANE_COLOR, rect, border_radius=6)
            pygame.draw.rect(self.screen, TARGET_LINE, rect, 2, border_radius=6)
            label = self.font.render(label_text, True, TEXT_COLOR)
            label_rect = label.get_rect(center=rect.center)
            self.screen.blit(label, label_rect)
        pygame.draw.line(self.screen, TARGET_LINE, (80, TARGET_Y), (SCREEN_WIDTH - 80, TARGET_Y), 2)

    def draw_notes(self) -> None:
        for note in self.notes:
            if note.missed:
                color = NOTE_MISS
            elif note.hit:
                color = NOTE_HIT
            else:
                color = NOTE_COLOR
            pygame.draw.circle(self.screen, color, (int(note.x), int(note.y)), 16)
            label = self.font.render(note.letter, True, BACKGROUND)
            rect = label.get_rect(center=(note.x, note.y))
            self.screen.blit(label, rect)

    def draw_hud(self) -> None:
        accuracy = 0
        total = self.hits + self.misses
        if total > 0:
            accuracy = math.floor((self.hits / total) * 100)
        hud_text = (
            f"Очки: {self.score}  Комбо: {self.combo}  Макс. Комбо: {self.max_combo}  "
            f"Точность: {accuracy}%  Уровень: {self.level}"
        )
        hud = self.font.render(hud_text, True, TEXT_COLOR)
        self.screen.blit(hud, (40, 20))

    def draw_intro(self) -> None:
        title = self.large_font.render("Пианорол", True, TEXT_COLOR)
        subtitle = self.font.render("Нажимайте буквы в момент касания линии", True, TEXT_COLOR)
        start = self.font.render("Нажмите пробел, чтобы начать", True, TEXT_COLOR)
        level_hint = self.font.render("Уровни 1-0: выбрать сложность", True, TEXT_COLOR)
        self.screen.blit(title, title.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 40)))
        self.screen.blit(subtitle, subtitle.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 4)))
        self.screen.blit(start, start.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 40)))
        self.screen.blit(level_hint, level_hint.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 76)))

    def run(self) -> None:
        playing = False
        while self.running:
            dt = self.clock.tick(FPS) / 1000
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                    if event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5,
                                     pygame.K_6, pygame.K_7, pygame.K_8, pygame.K_9, pygame.K_0):
                        level_map = {
                            pygame.K_1: 1,
                            pygame.K_2: 2,
                            pygame.K_3: 3,
                            pygame.K_4: 4,
                            pygame.K_5: 5,
                            pygame.K_6: 6,
                            pygame.K_7: 7,
                            pygame.K_8: 8,
                            pygame.K_9: 9,
                            pygame.K_0: 10,
                        }
                        self.set_level(level_map[event.key])
                    if not playing and event.key == pygame.K_SPACE:
                        playing = True
                        self.start_time = time.time()
                        self.last_spawn = time.time()
                        continue
                    if playing and event.unicode and event.unicode.upper() in self.lanes:
                        self.handle_hit(event.unicode.upper())

            self.screen.fill(BACKGROUND)
            self.draw_lanes()

            if playing:
                now = time.time()
                if now - self.last_spawn >= self.spawn_interval:
                    self.spawn_note()
                    self.last_spawn = now
                self.update_notes(dt)
                self.draw_notes()
                self.draw_hud()
            else:
                self.draw_intro()

            pygame.display.flip()

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    PianoRoll().run()
