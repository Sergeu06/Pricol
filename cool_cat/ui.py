from __future__ import annotations

import random
import time
from pathlib import Path

from PySide6 import QtCore, QtGui, QtWidgets

from . import config
from .cat_state import CatState
from .tts import TextToSpeech

ASSETS_DIR = Path(__file__).resolve().parent / "assets"
CAT_IMAGE_PATH = ASSETS_DIR / "cat.png"

HUNGRY_INSULTS_RU = [
    "Не до тебя. Сначала покорми.",
    "Отвали. Я голоден.",
    "Покорми — потом поговорим.",
    "Мне не до твоих слов. Еда нужна.",
    "Сначала миска, потом болтовня.",
    "Я не в настроении. Дай корм.",
    "Еда впереди — остальное потом.",
    "Текст? Ха. Я голоден.",
    "Пока пусто в миске — молчу.",
    "Кормить будешь? Тогда и поговорим.",
]

HUNGRY_INSULTS_EN = [
    "Not now. Feed me first.",
    "Buzz off. I'm hungry.",
    "Food first, talk later.",
    "No food, no words.",
    "Fill the bowl, then speak.",
    "I'm not in the mood. Feed me.",
    "I need food, not chatter.",
    "I'm hungry. Try again later.",
    "No bowl, no voice.",
    "Feed me, then we talk.",
]

PETTING_FULL_RU = [
    "Ну ладно, гладь. Но не увлекайся.",
    "Рука тёплая. Терпи, человек.",
    "Ладно, ты неплох. Пока.",
    "Мурчать не обещал, но приятно.",
    "Гладь и радуйся своей смелости.",
    "Нормально. Продолжай.",
    "Это заслужено. Я крут.",
    "Хорошо, но без фанатизма.",
]

PETTING_HUNGRY_RU = [
    "Гладь сколько хочешь, но я голоден.",
    "Руки убери и еду неси.",
    "Не до ласк. Миска где?",
    "Погладил — молодец. Теперь корми.",
    "Ладно, но я всё равно голоден.",
    "Тепло, но пусто. Дай корм.",
    "Сначала еда, потом нежности.",
    "Мур? Нет. Еда нужна.",
]

PETTING_FULL_EN = [
    "Fine, pet me. Don't get carried away.",
    "Your hand is warm. Acceptable.",
    "You're not bad. For now.",
    "I won't purr, but it's decent.",
    "Pet me and feel honored.",
    "Alright. Keep going.",
    "I deserve this. I'm cool.",
    "Okay, but no fan club.",
]

PETTING_HUNGRY_EN = [
    "Pet all you want, I'm still hungry.",
    "Hands off and bring food.",
    "No cuddles. Where's the bowl?",
    "Petting noted. Now feed me.",
    "Fine, but I'm still hungry.",
    "Warm hand, empty belly.",
    "Food first, affection later.",
    "Purr? Not without food.",
]

FEED_RU = [
    "Вот это другое дело.",
    "Нормально. Продолжай.",
    "Миска — это уважение.",
]

FEED_EN = [
    "Now that's better.",
    "Good. Keep it coming.",
    "A full bowl shows respect.",
]


class CoolCatWindow(QtWidgets.QMainWindow):
    def __init__(self, tts: TextToSpeech, cat_state: CatState) -> None:
        super().__init__()
        self.setWindowTitle("Крутой Кот")
        self.tts = tts
        self.cat_state = cat_state
        self._last_reply: dict[str, str] = {}
        self._last_tick = time.monotonic()

        central = QtWidgets.QWidget()
        self.setCentralWidget(central)

        main_layout = QtWidgets.QHBoxLayout(central)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(16)

        self.image_label = QtWidgets.QLabel()
        self.image_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMinimumSize(360, 360)
        self.image_label.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Expanding,
        )
        main_layout.addWidget(self.image_label, stretch=2)

        control_panel = QtWidgets.QWidget()
        control_layout = QtWidgets.QVBoxLayout(control_panel)
        control_layout.setSpacing(12)

        language_layout = QtWidgets.QHBoxLayout()
        language_label = QtWidgets.QLabel("Язык ответа:")
        self.language_combo = QtWidgets.QComboBox()
        self.language_combo.addItem("Русский", userData="ru")
        self.language_combo.addItem("English", userData="en")
        language_layout.addWidget(language_label)
        language_layout.addWidget(self.language_combo)
        control_layout.addLayout(language_layout)

        self.voice_status_label = QtWidgets.QLabel("")
        self.voice_status_label.setWordWrap(True)
        control_layout.addWidget(self.voice_status_label)

        satiety_layout = QtWidgets.QVBoxLayout()
        self.satiety_bar = QtWidgets.QProgressBar()
        self.satiety_bar.setRange(config.SATIETY_MIN, config.SATIETY_MAX)
        self.satiety_label = QtWidgets.QLabel("")
        satiety_layout.addWidget(self.satiety_bar)
        satiety_layout.addWidget(self.satiety_label)
        control_layout.addLayout(satiety_layout)

        buttons_layout = QtWidgets.QHBoxLayout()
        self.feed_button = QtWidgets.QPushButton("Покормить")
        self.pet_button = QtWidgets.QPushButton("Погладить")
        buttons_layout.addWidget(self.feed_button)
        buttons_layout.addWidget(self.pet_button)
        control_layout.addLayout(buttons_layout)

        self.text_input = QtWidgets.QLineEdit()
        self.text_input.setPlaceholderText("Текст для озвучки")
        control_layout.addWidget(self.text_input)

        self.error_label = QtWidgets.QLabel("")
        self.error_label.setStyleSheet("color: #ff8f8f;")
        control_layout.addWidget(self.error_label)

        self.speak_button = QtWidgets.QPushButton("Озвучить")
        control_layout.addWidget(self.speak_button)

        self.log_box = QtWidgets.QTextEdit()
        self.log_box.setReadOnly(True)
        control_layout.addWidget(self.log_box, stretch=1)

        main_layout.addWidget(control_panel, stretch=1)

        self.feed_button.clicked.connect(self.handle_feed)
        self.pet_button.clicked.connect(self.handle_pet)
        self.speak_button.clicked.connect(self.handle_speak)
        self.language_combo.currentIndexChanged.connect(self.update_voice_status)

        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.on_timer_tick)
        self.timer.start()

        self.update_voice_status()
        self.update_cat_image()
        self.refresh_satiety_ui()

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        super().resizeEvent(event)
        self.update_cat_image()

    def update_cat_image(self) -> None:
        if CAT_IMAGE_PATH.exists():
            pixmap = QtGui.QPixmap(str(CAT_IMAGE_PATH))
            if not pixmap.isNull():
                scaled = pixmap.scaled(
                    self.image_label.size(),
                    QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                    QtCore.Qt.TransformationMode.SmoothTransformation,
                )
                self.image_label.setPixmap(scaled)
                self.image_label.setText("")
                return
        self.image_label.setPixmap(QtGui.QPixmap())
        self.image_label.setText("Нет изображения")

    def current_language(self) -> str:
        return self.language_combo.currentData()

    def update_voice_status(self) -> None:
        info = self.tts.voice_info(self.current_language())
        if info.warning:
            self.voice_status_label.setText(f"Предупреждение: {info.warning}")
        elif info.name:
            self.voice_status_label.setText(f"Голос: {info.name}")
        else:
            self.voice_status_label.setText("Голос: системный по умолчанию")

    def refresh_satiety_ui(self) -> None:
        self.satiety_bar.setValue(self.cat_state.satiety)
        status = "ГОЛОДЕН" if self.cat_state.is_hungry() else "СЫТ"
        self.satiety_label.setText(f"Сытость: {self.cat_state.satiety}/100 — {status}")

    def add_log(self, message: str) -> None:
        self.log_box.append(message)

    def handle_feed(self) -> None:
        self.cat_state.feed()
        self.refresh_satiety_ui()
        reply = self.random_reply("feed", FEED_RU if self.current_language() == "ru" else FEED_EN)
        self.add_log(f"Кот: {reply}")
        self.tts.speak(reply, self.current_language())

    def handle_pet(self) -> None:
        if self.cat_state.is_hungry():
            replies = PETTING_HUNGRY_RU if self.current_language() == "ru" else PETTING_HUNGRY_EN
        else:
            replies = PETTING_FULL_RU if self.current_language() == "ru" else PETTING_FULL_EN
        reply = self.random_reply("pet", replies)
        self.add_log(f"Кот: {reply}")
        self.tts.speak(reply, self.current_language())

    def handle_speak(self) -> None:
        text = self.text_input.text().strip()
        if not text:
            self.error_label.setText("Введите текст для озвучки.")
            return
        self.error_label.setText("")
        if self.cat_state.is_hungry():
            replies = HUNGRY_INSULTS_RU if self.current_language() == "ru" else HUNGRY_INSULTS_EN
            reply = self.random_reply("hungry", replies)
            self.add_log(f"Кот: {reply}")
            self.tts.speak(reply, self.current_language())
            return
        self.add_log(f"Пользователь: {text}")
        self.add_log(f"Кот озвучил: {text}")
        self.tts.speak(text, self.current_language())
        self.text_input.clear()

    def random_reply(self, key: str, pool: list[str]) -> str:
        reply = random.choice(pool)
        last = self._last_reply.get(key)
        if last == reply and len(pool) > 1:
            alternatives = [item for item in pool if item != last]
            reply = random.choice(alternatives)
        self._last_reply[key] = reply
        return reply

    def on_timer_tick(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_tick
        self._last_tick = now
        if self.cat_state.tick(elapsed):
            self.refresh_satiety_ui()
