from .Base_command import BaseCommand


from .Base_command import BaseCommand


class MuteListeningCommand(BaseCommand):
    name = "режим прослушивания"
    aliases = [
        "выключи прослушивание",
        "включи прослушивание",
        "отключи микрофон",
        "включи микрофон",
        "режим mute",
        "режим анмут",
        "заглуши микрофон",
        "разглуши микрофон",
        "стоп прослушивание",
        "старт прослушивание",
        "пауза прослушивания",
        "продолжи прослушивание"
    ]

    def __init__(self, assistant=None, sound_player=None):
        super().__init__(assistant, sound_player)

    def execute(self, text: str, converted_text: str = None, *args, **kwargs):
        text_lower = text.lower()

        # Определяем действие на основе текста команды
        if any(word in text_lower for word in ["выключи", "отключи", "заглуши", "стоп", "пауза", "mute"]):
            self._mute_listening()
        elif any(word in text_lower for word in ["включи", "разглуши", "старт", "продолжи", "анмут"]):
            self._unmute_listening()
        else:
            # Если команда неясная - переключаем состояние
            self._toggle_listening()

    def _mute_listening(self):
        """Выключает прослушивание wake word через метод ассистента"""
        if self.assistant and hasattr(self.assistant, 'mute_listening'):
            success = self.assistant.wakeword_mute()
            if success:
                self.say("Прослушивание отключено. Я больше не буду реагировать на wake word.")
                self.play_sound("system_audio/mute.wav")
            else:
                self.say("Не могу отключить прослушивание.")
        else:
            self.say("Функция отключения прослушивания недоступна.")

    def _unmute_listening(self):
        """Включает прослушивание wake word через метод ассистента"""
        if self.assistant and hasattr(self.assistant, 'unmute_listening'):
            success = self.assistant.wakeword_unmute()
            if success:
                self.say("Прослушивание включено. Я снова реагирую на wake word.")
                self.play_sound("system_audio/unmute.wav")
            else:
                self.say("Не могу включить прослушивание.")
        else:
            self.say("Функция включения прослушивания недоступна.")

    def _toggle_listening(self):
        """Переключает состояние прослушивания через метод ассистента"""
        if self.assistant and hasattr(self.assistant, 'toggle_listening'):
            success = self.assistant.wakeword_toggle_mute()
            if success:
                # Получаем текущий статус для сообщения
                status = self.assistant.get_wakeword_status()
                if status.get('wakeword_active', False) and not status.get('manual_mute', False):
                    self.say("Прослушивание включено.")
                    self.play_sound("system_audio/unmute.wav")
                else:
                    self.say("Прослушивание отключено.")
                    self.play_sound("system_audio/mute.wav")
            else:
                self.say("Не могу переключить режим прослушивания.")
        else:
            self.say("Функция переключения прослушивания недоступна.")
