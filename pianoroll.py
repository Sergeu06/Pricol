import math
import random
import sys
import time
from dataclasses import dataclass

import pygame

SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 700
FPS = 60

BACKGROUND = (12, 12, 18)
LANE_COLOR = (32, 32, 46)
TARGET_LINE = (240, 240, 255)
NOTE_COLOR = (109, 226, 255)
NOTE_HIT = (126, 255, 153)
NOTE_MISS = (255, 109, 120)
TEXT_COLOR = (240, 240, 255)

ROWS = ["QWERTYUIOP", "ASDFGHJKL", "ZXCVBNM"]
ALL_LETTERS = "".join(ROWS)

LANE_TOP = 60
LANE_BOTTOM = SCREEN_HEIGHT - 140
TARGET_Y = LANE_BOTTOM - 10

SPAWN_INTERVAL = 0.45
FALL_SPEED = 320.0

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

        self.lanes = self._build_lanes()
        self.notes: list[Note] = []
        self.last_spawn = time.time()

        self.score = 0
        self.combo = 0
        self.max_combo = 0
        self.hits = 0
        self.misses = 0
        self.running = True
        self.start_time = time.time()

    def _build_lanes(self) -> dict[str, float]:
        lanes: dict[str, float] = {}
        available_width = SCREEN_WIDTH - 120
        for row_index, row in enumerate(ROWS):
            row_width = available_width * (len(row) / len(ROWS[0]))
            start_x = (SCREEN_WIDTH - row_width) / 2
            gap = row_width / len(row)
            for i, letter in enumerate(row):
                lanes[letter] = start_x + i * gap + gap / 2
        return lanes

    def spawn_note(self) -> None:
        letter = random.choice(ALL_LETTERS)
        x = self.lanes[letter]
        self.notes.append(Note(letter=letter, x=x, y=LANE_TOP - 40))

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
            note.y += FALL_SPEED * dt
            if note.y > TARGET_Y + WINDOWS["good"]:
                note.missed = True
                self.register_miss()
        self.notes = [note for note in self.notes if note.y < SCREEN_HEIGHT + 60]

    def draw_lanes(self) -> None:
        for letter, x in self.lanes.items():
            pygame.draw.line(self.screen, LANE_COLOR, (x, LANE_TOP), (x, LANE_BOTTOM), 3)
            label = self.font.render(letter, True, TEXT_COLOR)
            rect = label.get_rect(center=(x, LANE_BOTTOM + 24))
            self.screen.blit(label, rect)
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
        hud_text = f"Очки: {self.score}  Комбо: {self.combo}  Макс. Комбо: {self.max_combo}  Точность: {accuracy}%"
        hud = self.font.render(hud_text, True, TEXT_COLOR)
        self.screen.blit(hud, (40, 20))

    def draw_intro(self) -> None:
        title = self.large_font.render("Пианорол", True, TEXT_COLOR)
        subtitle = self.font.render("Нажимайте буквы в момент касания линии", True, TEXT_COLOR)
        start = self.font.render("Нажмите пробел, чтобы начать", True, TEXT_COLOR)
        self.screen.blit(title, title.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 40)))
        self.screen.blit(subtitle, subtitle.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 4)))
        self.screen.blit(start, start.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 40)))

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
                if now - self.last_spawn >= SPAWN_INTERVAL:
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
