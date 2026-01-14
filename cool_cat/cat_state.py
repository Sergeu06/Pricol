from dataclasses import dataclass, field

from . import config


@dataclass
class CatState:
    satiety: int = config.SATIETY_START
    threshold_hungry: int = config.HUNGRY_THRESHOLD
    _decay_elapsed: float = field(default=0.0, init=False, repr=False)

    def is_hungry(self) -> bool:
        return self.satiety < self.threshold_hungry

    def feed(self) -> None:
        self.satiety = min(config.SATIETY_MAX, self.satiety + config.SATIETY_FEED_AMOUNT)

    def tick(self, elapsed_seconds: float) -> bool:
        if elapsed_seconds <= 0:
            return False
        self._decay_elapsed += elapsed_seconds
        changed = False
        while self._decay_elapsed >= config.SATIETY_DECAY_INTERVAL:
            self._decay_elapsed -= config.SATIETY_DECAY_INTERVAL
            if self.satiety > config.SATIETY_MIN:
                self.satiety -= 1
                changed = True
        return changed
