# commands/TimeCommand.py
from datetime import datetime
from .Base_command import BaseCommand


class TimeCommand(BaseCommand):
    name = "время"
    aliases = ["время", "который час", "скажи время", "сколько сейчас времени", "сколько время"]

    def __init__(self, assistant=None, sound_player=None):
        super().__init__(assistant, sound_player)  # ← ОБЯЗАТЕЛЬНО В КАЖДОЙ КОМАНДЕ

    def execute(self, text: str, *args, **kwargs):
        now = datetime.now().strftime("%H:%M")
        response = f"Сейчас {now}"
        print(response)

        # Используем метод say для отправки ответа в веб-интерфейс
        self.say(response)
