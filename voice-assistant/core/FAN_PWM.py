import wiringpi as GPIO
import time
import subprocess
import sys
import os
import json
import paho.mqtt.client as mqtt
from threading import Lock
import datetime
from threading import Lock, Thread  # ИЗМЕНЕНО(1): Добавлен импорт Thread

# Конфигурация
PWM_PIN = 21  # GPIO 6 (WiringPi) - основной PWM-пин для Orange Pi
RPS_PIN = 19  # wPi 19 (GPIO 256) для датчика RPS ЧИСЛО ОБОРОТОВ В СЕКУНДУ, те в реальный момент
PWM_RANGE = 1024  # Стандартный диапазон для WiringPi
MIN_PWM = 950  # Минимальное значение для запуска вентилятора
MAX_PWM = 1024  # Максимальное значение PWM
PWM_DEAD_ZONE = 5  # Если после расчётов PWM изменился на число больше этого, тогда обновляем pwm на PWM_PIN
TEMP_CHECK_INTERVAL = 5  # Время интервала сканирования температуры в секундах
OFF_TEMP = 30  # Температура выключения вентилятора
MAX_TEMP = 65  # Температура при которой вентилятор будет крутится на 100% т.е. pwm = PWM_RANGE(1024)

# Константы для расчета RPS
FAN_PULSES_PER_REVOLUTION = 2  # Обычно 2 импульса на оборот (может отличаться для вашего вентилятора)
RPS_MEASUREMENT_INTERVAL = 1.0  # Интервал измерения RPS в секундах
DEBOUNCE_TIME = 0.005  # 5 мс защита от дребезга

fan_rps = 0  # Заглушка для будущего датчика
pulse_count = 0  # Автоматически защищен от race condition (состояния гонки в многопоточности)
last_pulse_time = 0
rps_lock = Lock()

# MQTT-настройки
MQTT_BROKER = "192.168.0.33"  # Например, "localhost" или IP
MQTT_PORT = 1883
MQTT_USER = "mqtt-user"
MQTT_PASSWORD = "F7SKJ$@#5DSf23"
MQTT_BASE_TOPIC = "home/orangepi/fan_control"
MQTT_CLIENT_ID = "orangepi_fan_controller"

# Глобальные переменные
mqtt_connected = False
mqtt_client = None  # ИЗМЕНЕНО(2): Глобальная переменная для MQTT-клиента


def setup_gpio():
    """Настройка GPIO и PWM"""
    pass

def pulse_interrupt():
    """Обработчик прерывания с защитой от дребезга"""
    pass

def calculate_rps():
    """Рассчитать обороты в секунду (RPS) в реальном времени"""
    pass

def get_cpu_temp():
    """Получить температуру CPU в °C"""
    pass

def set_fan_speed(pwm_value):
    """Установить скорость вентилятора через PWM"""
    pass

def calculate_pwm(temp):
    """Вычислить значение PWM на основе температуры"""
    pass

def clear_screen():
    """Очистить экран терминала (если возможно)"""
    if os.isatty(sys.stdout.fileno()):  # Проверяем, что вывод идет в терминал
        os.system('clear')

def display_info(temp, pwm_value, pin, rps):
    """Отобразить информацию о состоянии"""
    # clear_screen()
    print("===== Управление вентилятором Orange Pi Zero 2W =====")
    print(f"Температура CPU: {temp:.1f}°C")
    print(f"Значение PWM: {int(pwm_value)}/{PWM_RANGE}")
    print(f"Процент мощности: {pwm_value / MAX_PWM * 100:.1f}%")
    print(f"Реальная скорость вентилятора: {int(rps)} RPS")
    print(f"GPIO пин: {pin} (PWM)")
    print(f"Состояние: {'ВКЛ' if pwm_value >= MIN_PWM else 'ВЫКЛ'}")
    print(f"MIN_PWM: {MIN_PWM}, MAX_PWM: {MAX_PWM}")
    print("\nНажмите Ctrl+C для выхода")
    print("=" * 55)

# MQTT-функции
def publish_availability(client, online=True):
    client.publish(
        f"{MQTT_BASE_TOPIC}/status",
        payload="online" if online else "offline",
        retain=True
    )

def on_connect(client, userdata, flags, reason_code, properties=None):
    global mqtt_connected
    if reason_code == 0:
        print("Успешное подключение к MQTT брокеру")
        mqtt_connected = True
        # Подписка на команды
        client.subscribe("home/orangepi/fan_control/set/#")
        # Публикация статуса доступности
        publish_availability(client, True)
        # Публикация текущих настроек
        publish_config(client)
    else:
        print(f"Ошибка подключения MQTT: {reason_code}")
        ###mqtt_connected = False


def on_disconnect(client, userdata, disconnect_flags, reason_code, properties=None):
    global mqtt_connected
    mqtt_connected = False
    print(f"Отключение от MQTT брокера (код: {reason_code}, флаги: {disconnect_flags})")
    publish_availability(client, False)


def on_message(client, userdata, msg):
    global MIN_PWM, MAX_PWM, OFF_TEMP, MAX_TEMP

    try:
        payload = msg.payload.decode()
        if msg.topic.endswith("set/pwm/min"):
            MIN_PWM = int(payload)
            client.publish(f"{MQTT_BASE_TOPIC}/pwm/min", MIN_PWM, retain=True)

        elif msg.topic.endswith("set/pwm/max"):
            MAX_PWM = int(payload)
            client.publish(f"{MQTT_BASE_TOPIC}/pwm/max", MAX_PWM, retain=True)

        elif msg.topic.endswith("set/temp/off"):
            OFF_TEMP = float(payload)
            client.publish(f"{MQTT_BASE_TOPIC}/temp/off", OFF_TEMP, retain=True)

        elif msg.topic.endswith("set/temp/max"):
            MAX_TEMP = float(payload)
            client.publish(f"{MQTT_BASE_TOPIC}/temp/max", MAX_TEMP, retain=True)

    except ValueError as e:
        print(f"Ошибка обработки команды: {e}")


def publish_config(client):
    """Публикация текущих настроек"""
    config = {
        "pwm/min": MIN_PWM,
        "pwm/max": MAX_PWM,
        "temp/off": OFF_TEMP,
        "temp/max": MAX_TEMP
    }

    for key, value in config.items():  # Исправлено на .items()
        client.publish(
            f"{MQTT_BASE_TOPIC}/{key}",
            payload=str(value),
            retain=True,
            qos=1
        )


def publish_state(client, temp, pwm_value, rps):
    """Публикация текущего состояния"""
    state = {
        "temperature": temp,
        "pwm": pwm_value,
        "rps": rps,
        "fan_percent": pwm_value / MAX_PWM * 100,
        "fan_status": 1 if pwm_value >= MIN_PWM else 0
    }

    # Основной топик состояния
    client.publish(
        f"{MQTT_BASE_TOPIC}/state",
        json.dumps(state),
        retain=True
    )

    # Отдельные топики для графиков
    client.publish(f"{MQTT_BASE_TOPIC}/sensors/cpu_temp", round(temp, 2))
    client.publish(f"{MQTT_BASE_TOPIC}/sensors/fan_rps", round(rps, 2))
    client.publish(f"{MQTT_BASE_TOPIC}/pwm/current", round(pwm_value, 2))


# ИЗМЕНЕНО(3): Функция для фонового потока MQTT
def mqtt_background_thread():


    # Создаем и настраиваем клиент
    mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, MQTT_CLIENT_ID)
    mqtt_client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
    mqtt_client.on_connect = on_connect
    mqtt_client.on_disconnect = on_disconnect
    mqtt_client.on_message = on_message
    mqtt_client.reconnect_delay_set(min_delay=10, max_delay=40)

    # Для отладки (можно закомментировать)
    mqtt_client.on_socket_open = lambda client, userdata, sock: print("MQTT: Сокет открыт")
    mqtt_client.on_socket_close = lambda client, userdata, sock: print("MQTT: Сокет закрыт")

    # Бесконечный цикл подключения/переподключения
    while True:
        try:
            if not mqtt_connected:
                print("Попытка подключения к MQTT брокеру...")
                mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
                mqtt_client.loop_start()
            time.sleep(5)  # Проверяем соединение каждые 5 секунд
        except Exception as e:
            print(f"Ошибка MQTT: {e}")
            time.sleep(5)


def main():
    global mqtt_connected, fan_rps, pulse_count
    # fan_rps = -88

    # ИЗМЕНЕНО(4): Запускаем MQTT в фоновом потоке
    mqtt_thread = Thread(target=mqtt_background_thread, daemon=True)
    mqtt_thread.start()
    # Даем время на инициализацию MQTT
    time.sleep(1)

    try:
        # Проверка прав
        if os.geteuid() != 0:
            print("Требуются права root. Запустите скрипт с sudo.")
            sys.exit(1)

        # Настройка PWM
        if not setup_gpio():
            print("Не удалось настроить PWM. Проверьте пин GPIO.")
            sys.exit(1)

        # Начальное состояние
        last_pwm = -1
        last_rps_time = time.time()
        actual_pwm = 0  # ДОБАВИЛ ТК НЕБЫЛО ИНИЦ. НЕПРОТЕСТИРОВАННО!
        print(f"Управление вентилятором через GPIO {PWM_PIN} (PWM)")
        print(f"Датчик RPS стоит на GPIO {RPS_PIN}")
        print(f"MIN_PWM={MIN_PWM}, MAX_PWM={MAX_PWM}, OFF_TEMP={OFF_TEMP}°C")
        print("Нажмите Ctrl+C для выхода\n")

        while True:
            current_time = time.time()
            temp = get_cpu_temp()
            pwm_value = calculate_pwm(temp)

            # Обновляем RPS каждые RPS_MEASUREMENT_INTERVAL секунд
            if current_time - last_rps_time >= RPS_MEASUREMENT_INTERVAL:
                fan_rps = calculate_rps()
                last_rps_time = current_time

            # Обновляем PWM только при:
            # 1. Включении/выключении
            # 2. Значительном изменении скорости
            # PWM_DEAD_ZONE не блокирует включение/выключение! Он влияет только на изменения скорости при уже работающем вентиляторе

            # 1. Выключение (было ≠0, стало 0) # 2. Включение (было <MIN, стало ≥MIN) # 3. Значительное изменение скорости
            if (pwm_value == 0 and last_pwm != 0) or (pwm_value >= MIN_PWM and last_pwm < MIN_PWM) or (
                    abs(pwm_value - last_pwm) > PWM_DEAD_ZONE):
                actual_pwm = set_fan_speed(pwm_value)
                last_pwm = actual_pwm

            # ИЗМЕНЕНО(1): Публикация состояния через глобальный mqtt_client
            if mqtt_connected and mqtt_client is not None:
                try:
                    publish_state(mqtt_client, temp, actual_pwm, fan_rps)
                except Exception as e:
                    print(f"Ошибка публикации состояния: {e}")

            display_info(temp, actual_pwm, PWM_PIN, fan_rps)
            time.sleep(TEMP_CHECK_INTERVAL)

    except KeyboardInterrupt:
        print("\nОстановка скрипта...")
    except Exception as e:
        print(f"Критическая ошибка: {e}")
    finally:
        set_fan_speed(0)

        if mqtt_connected:
            mqtt_client.publish(f"{MQTT_BASE_TOPIC}/status", "offline", retain=True)
            mqtt_client.disconnect()
            mqtt_client.loop_stop()

        print("Вентилятор выключен. Скрипт завершен.")


if __name__ == "__main__":
    main()
