import os
import time
import json
import sys
import asyncio
from threading import Thread

import paho.mqtt.client as paho_mqtt


class MQTT_SENDLER_CLASS:
    def __init__(self,
                 mqtt_broker_ip_address="ВАШ_АДРЕС_MQTT_БРОКЕРА",
                 mqtt_port=1883,
                 mqtt_username="ВАШ_MQTT_USER",
                 mqtt_password="ВАШ_MQTT_PASSWORD",
                 mqtt_base_topic="home/orangepi/AFINA_Assistant"):

        # ------------------ Настройки брокера ------------------
        self.MQTT_CLIENT_ID = "orangepi_AFINA_Assistant"
        self.mqtt_broker_ip_address = mqtt_broker_ip_address
        self.mqtt_port = mqtt_port
        self.mqtt_username = mqtt_username
        self.mqtt_user_password = mqtt_password
        self.mqtt_base_topic = mqtt_base_topic

        # ------------------ Сущности и флаги -------------------
        self.mqtt_connected = False
        self.MQTT_CLIENT = None

    def publish_availability(self, client, online=True):
        client.publish(
            f"{self.mqtt_base_topic}/status",
            payload="online" if online else "offline",
            retain=True
        )

    def on_connect(self, client, userdata, flags, reason_code, properties=None):
        if reason_code == 0:
            print("Успешное подключение к MQTT брокеру")
            self.mqtt_connected = True
            # Подписка на команды
            #client.subscribe("home/orangepi/fan_control/set/#")
            # Публикация статуса доступности
            self.publish_availability(client, True)
            # Публикация текущих настроек
            #publish_config(client)
        else:
            print(f"Ошибка подключения MQTT: {reason_code}")
            ###mqtt_connected = False

    def on_disconnect(self, client, userdata, disconnect_flags, reason_code, properties=None):
        self.mqtt_connected = False
        print(f"Отключение от MQTT брокера (код: {reason_code}, флаги: {disconnect_flags})")
        self.publish_availability(client, False)

    def on_message(self, client, userdata, msg):
        try:
            payload = msg.payload.decode()
            if msg.topic.endswith("set/pwm/min"):
                MIN_PWM = int(payload)
                client.publish(topic=f"{self.mqtt_base_topic}/pwm/min", payload=MIN_PWM, retain=True)

        except ValueError as e:
            print(f"Ошибка обработки команды: {e}")

    def mqtt_background_thread(self):
        # Создаем и настраиваем клиент
        self.MQTT_CLIENT = paho_mqtt.Client(client_id=self.MQTT_CLIENT_ID)
        self.MQTT_CLIENT.username_pw_set(self.mqtt_username, self.mqtt_user_password)
        self.MQTT_CLIENT.on_connect = self.on_connect
        self.MQTT_CLIENT.on_disconnect = self.on_disconnect
        self.MQTT_CLIENT.on_message = self.on_message
        self.MQTT_CLIENT.reconnect_delay_set(min_delay=10, max_delay=40)

        # Для отладки (можно закомментировать)
        #self.MQTT_CLIENT.on_socket_open = lambda client, userdata, sock: print("MQTT: Сокет открыт")
        #self.MQTT_CLIENT.on_socket_close = lambda client, userdata, sock: print("MQTT: Сокет закрыт")

        # Бесконечный цикл подключения/переподключения
        while True:
            try:
                if not self.mqtt_connected:
                    print("Попытка подключения к MQTT брокеру...")
                    self.MQTT_CLIENT.connect(self.mqtt_broker_ip_address, self.mqtt_port, 60)
                    self.MQTT_CLIENT.loop_start()
                time.sleep(5)  # Проверяем соединение каждые 5 секунд
            except Exception as e:
                print(f"Ошибка MQTT: {e}")
                time.sleep(5)

    def publish_data(self, topic_suffix, payload, retain=True):
        """
        Публикует данные в MQTT.
        topic_suffix: часть топика после базового
        payload: данные для отправки
        retain: удерживать сообщение на брокере
        """
        if not self.MQTT_CLIENT or not self.mqtt_connected:
            print("[MQTT] MQTT не подключён, данные не отправлены")
            return

        full_topic = f"{self.mqtt_base_topic}/{topic_suffix}"

        # Если на вход пришел список или словарь тогда его в JSON, иначе как строку отправляем
        if isinstance(payload, (dict, list)):
            payload_to_send = json.dumps(payload)
        else:
            payload_to_send = str(payload)

        self.MQTT_CLIENT.publish(full_topic, payload=payload_to_send, retain=retain)
        print(f"[MQTT] Published to {full_topic}: {payload_to_send}")


def main():
    mqtt_sendler_class = MQTT_SENDLER_CLASS()
    mqtt_thread = Thread(target=mqtt_sendler_class.mqtt_background_thread, daemon=True)  # без скобок
    mqtt_thread.start()

    # Даем время на инициализацию MQTT
    time.sleep(1)

    while True:
        time.sleep(8)
        mqtt_sendler_class.publish_data("queue_commands_from_voice_assistant/tasks_on_phone/set_alarm", {"hours": 6, "minutes": 32})

if __name__ == "__main__":
    main()
