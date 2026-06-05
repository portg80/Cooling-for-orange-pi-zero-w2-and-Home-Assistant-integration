from datetime import datetime
import re
from .Base_command import BaseCommand

class FindMyPhone(BaseCommand):
    name = "найди мой телефон"
    aliases = [
        "найди мой телефон",
        "где мой телефон",
        "я потерял телефон",
        "найти телефон",
        "где телефон",
        "позвони на мой телефон",
        "включи сигнал на телефоне"
    ]

    def __init__(self, mqtt_sendler_class=None, assistant=None, sound_player=None):
        super().__init__(assistant, sound_player)  # ← ОБЯЗАТЕЛЬНО В КАЖДОЙ КОМАНДЕ
        self.mqtt_sendler_class = mqtt_sendler_class

    def execute(self, text: str, converted_text: str = None,  *args, **kwargs):
        if self.mqtt_sendler_class:
            self.mqtt_sendler_class.publish_data(
                "queue_commands_from_voice_assistant/tasks_on_phone/find_my_phone",
                {"Finding?": True}
            )
            self.say(f"[MQTT] \"Звоню\" на ваш телефон (через таймер). Идите на звук")
            print(f"[MQTT] \"Звоню\" на ваш телефон (через таймер). Идите на звук")
        else:
            self.say(f"[MQTT] MQTT не инициализирован")
            print("[MQTT] MQTT не инициализирован")
