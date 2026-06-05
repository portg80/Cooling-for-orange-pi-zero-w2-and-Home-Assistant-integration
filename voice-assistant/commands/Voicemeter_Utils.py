import voicemeeterlib
from typing import Any

class Voicemeter_Utils:
    headphones_channel = "A2"
    speakers_channel = "A1"

    """Главный канал переключить в наушники"""
    @staticmethod
    def main_set_headphones():
        try:
            with voicemeeterlib.api('potato') as vm:
                vm.strip[7].A1 = False
                vm.strip[7].A2 = True
        except Exception as e:
            print(f"Ошибка переключения Voicemeeter: {e}")
