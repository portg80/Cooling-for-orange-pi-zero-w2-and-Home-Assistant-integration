from datetime import datetime
import re
from .Base_command import BaseCommand

class SetAlarmCommand(BaseCommand):
    name = "установить будильник"
    aliases = ["установи будильник", "поставь будильник", "будильник на", "заведи будильник на"]


    def __init__(self, mqtt_sendler_class=None, assistant=None, sound_player=None):
        super().__init__(assistant, sound_player)  # ← ОБЯЗАТЕЛЬНО В КАЖДОЙ КОМАНДЕ
        self.mqtt_sendler_class = mqtt_sendler_class

    def execute(self, text: str, converted_text: str = None,  *args, **kwargs):
        # Находим все числа в тексте
        numbers = [int(n) for n in re.findall(r'\d+', converted_text)]

        if len(numbers) >= 2:
            hours, minutes = numbers[0], numbers[1]
        else:
            self.say(f"[ERROR] Не удалось распознать время из команды. ({numbers}) в тексте: {converted_text}")
            print(f"[ERROR] Не удалось распознать время из команды. ({numbers}) в тексте: {converted_text}")
            return

        if self.mqtt_sendler_class:
            self.mqtt_sendler_class.publish_data(
                "queue_commands_from_voice_assistant/tasks_on_phone/set_alarm",
                {"hours": hours, "minutes": minutes}
            )
            self.say(f"[MQTT] Будильник отправлен: {hours}:{minutes}")
            print(f"[MQTT] Будильник отправлен: {hours}:{minutes}")
        else:
            self.say(f"[MQTT] MQTT не инициализирован")
            print("[MQTT] MQTT не инициализирован")
