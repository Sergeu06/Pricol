from cool_cat import config
from cool_cat.cat_state import CatState


def test_feed_caps_at_max() -> None:
    state = CatState(satiety=config.SATIETY_MAX - 5)
    state.feed()
    assert state.satiety == config.SATIETY_MAX


def test_tick_reduces_satiety_over_time() -> None:
    state = CatState(satiety=50)
    changed = state.tick(config.SATIETY_DECAY_INTERVAL + 0.1)
    assert changed is True
    assert state.satiety == 49


def test_is_hungry_threshold() -> None:
    state = CatState(satiety=config.HUNGRY_THRESHOLD - 1)
    assert state.is_hungry() is True
