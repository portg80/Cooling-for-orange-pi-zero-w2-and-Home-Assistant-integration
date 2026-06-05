# commands/GreetingCommand.py
from .Base_command import BaseCommand


class GreetingCommand(BaseCommand):
    name = "привет"
    aliases = ["привет", "здравствуй", "добрый день", "хай"]

    def __init__(self, assistant=None, sound_player=None):
        super().__init__(assistant, sound_player)  # ← ОБЯЗАТЕЛЬНО В КАЖДОЙ КОМАНДЕ

    def execute(self, text: str, *args, **kwargs):
        responses = [
            "Привет! Чем могу помочь?",
            "Здравствуйте! Готов к вашим командам.",
            "Приветствую! Слушаю вас."
        ]
        import random
        response = random.choice(responses)
        print(response)

        self.play_random_sound("say/hello", use_all_files=True)
        self.say(response)
