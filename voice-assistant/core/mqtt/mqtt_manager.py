import json
from typing import Dict, Any

class MqttManager:
    def __init__(self, mqtt_client, base_topic: str):
        self.mqtt_client = mqtt_client            # Экземпляр AsyncMQTTClient
        self.base_topic = base_topic.rstrip("/")  # Базовый префикс всех топиков (например, "home/assistant")

    async def publish_nested(self, subtopics: list[str], payload: Any):
        """
        Публикует сообщение в иерархию сабтопиков, например:
        subtopics = ["voice_assistant", "set_alarm", "10:30"]
        -> публикуем в "base_topic/voice_assistant/set_alarm/10:30"
        """
        topic = "/".join([self.base_topic] + subtopics)  # Формируем полный путь
        if not isinstance(payload, str):
            payload = json.dumps(payload)                # Если не строка — сериализуем в JSON
        await self.mqtt_client.publish(topic, payload)   # Отправляем через AsyncMQTTClient
