# commands/DateCommand.py
from datetime import datetime
from .Base_command import BaseCommand

class DateCommand(BaseCommand):
    name = "дата"
    aliases = ["дата", "какое сегодня число", "какой сегодня день", "скажи дату"]

    def __init__(self, assistant=None, sound_player=None):
        super().__init__(assistant, sound_player)  # ← ОБЯЗАТЕЛЬНО В КАЖДОЙ КОМАНДЕ

    def execute(self, text: str, *args, **kwargs):
        today = datetime.now().strftime("%d.%m.%Y")
        response = f"Сегодня {today}"
        print(response)
        self.say(response)
