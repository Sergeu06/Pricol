import sys

from PySide6 import QtWidgets

from .cat_state import CatState
from .tts import TextToSpeech
from .ui import CoolCatWindow


def main() -> int:
    app = QtWidgets.QApplication(sys.argv)
    tts = TextToSpeech()
    cat_state = CatState()
    window = CoolCatWindow(tts=tts, cat_state=cat_state)
    window.resize(1200, 860)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
