from .Base_command import BaseCommand


class ListeningStatusCommand(BaseCommand):
    name = "статус прослушивания"
    aliases = [
        "статус микрофона",
        "проверь прослушивание",
        "какой режим",
        "слушаешь ли ты"
    ]

    def __init__(self, assistant=None, sound_player=None):
        super().__init__(assistant, sound_player)

    def execute(self, text: str, converted_text: str = None, *args, **kwargs):
        status = self._get_detailed_status()
        self.say(status)

        # Визуальный статус в веб-интерфейс
        if hasattr(self.assistant, 'web_interface'):
            self.assistant.web_interface.send_assistant_response(
                f"📊 {status}",
                "system"
            )

    def _get_detailed_status(self):
        """Возвращает детальный статус системы"""
        if not self.assistant:
            return "Статус недоступен"

        status_parts = []

        # Получаем статус через метод ассистента
        if hasattr(self.assistant, 'get_listening_status'):
            status_data = self.assistant.get_wakeword_status()

            wakeword_active = status_data.get('wakeword_active', False)
            manual_mute = status_data.get('manual_mute', False)
            state = status_data.get('state_assistant_vosk', 'UNKNOWN')

            wakeword_status = "активно" if wakeword_active else "приостановлено"
            status_parts.append(f"Прослушивание wake word: {wakeword_status}")

            mode_status = "ручное отключение" if manual_mute else "автоматический"
            status_parts.append(f"Режим: {mode_status}")

            status_parts.append(f"Состояние: {state}")
        else:
            status_parts.append("Статус прослушивания: недоступен")

        # Активная команда
        if hasattr(self.assistant, 'active'):
            command_status = "активна" if self.assistant.active else "нет"
            status_parts.append(f"Текущая команда: {command_status}")

        return "Статус системы: " + ", ".join(status_parts)
