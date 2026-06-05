from .Base_command import BaseCommand
from .Voicemeter_Utils import Voicemeter_Utils

class VoicemeterCommand(BaseCommand):
    name = "Voicemeter главный в наушники"
    aliases = ["микшер главный в наушники", "микшер главный канал на наушники", "микшер главный канал наушники"]

    def __init__(self, assistant=None, sound_player=None):
        super().__init__(assistant, sound_player)  # ← ОБЯЗАТЕЛЬНО В КАЖДОЙ КОМАНДЕ


    def execute(self, text: str,  *args, **kwargs):
        Voicemeter_Utils.main_set_headphones()
