from __future__ import annotations

import platform
import subprocess
from dataclasses import dataclass
from typing import Iterable


@dataclass
class VoiceInfo:
    name: str | None
    warning: str | None = None


class TextToSpeech:
    def __init__(self) -> None:
        self._platform = platform.system().lower()
        self._ru_voice = VoiceInfo(name=None)
        self._en_voice = VoiceInfo(name=None)
        if self._platform == "darwin":
            self._load_voices()
        else:
            self._ru_voice = VoiceInfo(
                name=None,
                warning="Озвучка доступна только на macOS (say).",
            )
            self._en_voice = VoiceInfo(
                name=None,
                warning="Озвучка доступна только на macOS (say).",
            )

    def _load_voices(self) -> None:
        try:
            result = subprocess.run(
                ["say", "-v", "?"],
                check=True,
                capture_output=True,
                text=True,
            )
        except (subprocess.CalledProcessError, FileNotFoundError) as exc:
            message = f"Не удалось получить список голосов: {exc}"
            self._ru_voice = VoiceInfo(name=None, warning=message)
            self._en_voice = VoiceInfo(name=None, warning=message)
            return

        voices = list(self._parse_voices(result.stdout.splitlines()))
        self._ru_voice = self._pick_voice(voices, preferred="Yuri", locales=("ru_", "ru-"))
        self._en_voice = self._pick_voice(voices, preferred="Alex", locales=("en_", "en-"))

    @staticmethod
    def _parse_voices(lines: Iterable[str]) -> Iterable[tuple[str, str]]:
        for line in lines:
            parts = line.split()
            if len(parts) < 2:
                continue
            yield parts[0], parts[1]

    @staticmethod
    def _pick_voice(
        voices: list[tuple[str, str]],
        preferred: str,
        locales: tuple[str, ...],
    ) -> VoiceInfo:
        for name, locale in voices:
            if name.lower() == preferred.lower():
                return VoiceInfo(name=name)
        for name, locale in voices:
            if locale.lower().startswith(locales):
                return VoiceInfo(name=name)
        if voices:
            return VoiceInfo(name=None, warning="Не найден подходящий голос, используется системный по умолчанию.")
        return VoiceInfo(name=None, warning="Список голосов пуст.")

    def voice_info(self, language: str) -> VoiceInfo:
        if language == "ru":
            return self._ru_voice
        return self._en_voice

    def speak(self, text: str, language: str) -> bool:
        if self._platform != "darwin":
            return False
        voice = self.voice_info(language).name
        command = ["say"]
        if voice:
            command.extend(["-v", voice])
        command.append(text)
        try:
            subprocess.run(command, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
        return True
