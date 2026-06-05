import asyncio          # Модуль для асинхронного программирования (await, event loop)
import logging          # Для логирования ошибок и статусов
import aiomqtt          # Асинхронная библиотека для работы с MQTT-протоколом

logger = logging.getLogger(__name__)  # Создаём логгер для вывода сообщений в консоль/файл

class AsyncMQTTClient:
    def __init__(self, config):
        self.config = config                # Конфигурация (адрес брокера, порт, логин, пароль)
        self._client = None                 # Ссылка на экземпляр aiomqtt.Client после подключения
        self._connected = asyncio.Event()   # Событие, указывающее, что клиент подключен
        self._handlers = {}                 # Словарь: {топик -> асинхронный callback-функция}
        self._task = None                   # Задача asyncio для фонового подключения
        self._reconnect_delay = getattr(config, "MQTT_RECONNECT_DELAY", 5)  # Пауза между попытками reconnect

    async def connect_loop(self):
        """
        Основной цикл подключения и переподключения к MQTT брокеру.
        Работает в фоне, автоматически восстанавливает соединение.
        """
        client_opts = {
            "hostname": self.config.mqtt_broker_ip_address,   # Адрес брокера
            "port": self.config.mqtt_port,         # Порт (обычно 1883)
        }
        # Если заданы пользователь и пароль — добавляем в параметры
        if getattr(self.config, "MQTT_USER", None):
            client_opts["username"] = self.config.mqtt_username
        if getattr(self.config, "MQTT_PASSWORD", None):
            client_opts["password"] = self.config.mqtt_user_password
        if getattr(self.config, "MQTT_CLIENT_ID", None):
            client_opts["identifier"] = self.config.MQTT_CLIENT_ID

        # Бесконечный цикл для переподключения при обрыве связи.
        while True:
            try:
                # Подключаемся к брокеру
                async with aiomqtt.Client(**client_opts) as client:
                    self._client = client

                    # Подписываемся на все ранее зарегистрированные топики
                    for t in list(self._handlers.keys()):
                        await client.subscribe(t)

                    # Отмечаем, что подключение успешно
                    self._connected.set()
                    logger.info("MQTT connected")

                    # Асинхронный цикл чтения входящих сообщений
                    async for message in client.messages:
                        topic = str(message.topic)                     # Имя топика
                        payload = message.payload.decode(errors="ignore")  # Тело сообщения (декодируем байты)
                        cb = self._handlers.get(topic)                  # Проверяем, есть ли обработчик для топика
                        if cb:
                            try:
                                await cb(topic, payload)                # Вызываем обработчик
                            except Exception as e:
                                logger.exception("Handler error for %s: %s", topic, e)
            except Exception as e:
                # Ошибка соединения — ждём несколько секунд и пробуем снова
                logger.warning("MQTT connection error: %s — reconnect in %s s", e, self._reconnect_delay)
                self._connected.clear()  # Сбрасываем флаг подключения
                await asyncio.sleep(self._reconnect_delay)

    def start(self, loop: asyncio.AbstractEventLoop):
        """Запускает connect_loop как фоновую задачу в указанном event loop."""
        if self._task is None or self._task.done():
            self._task = loop.create_task(self.connect_loop())

    async def publish(self, topic: str, payload: str, qos: int = 0, retain: bool = False):
        """Публикует сообщение в указанный топик."""
        await self._connected.wait()  # Дожидаемся подключения
        try:
            # Отправляем сообщение брокеру
            await self._client.publish(topic, payload.encode(), qos=qos, retain=retain)
        except Exception as e:
            logger.exception("Publish failed: %s", e)

    async def subscribe(self, topic: str, callback):
        """
        Регистрирует обработчик (асинхронную функцию) для топика.
        Если клиент уже подключён, сразу подписывается.
        """
        self._handlers[topic] = callback
        if self._connected.is_set():
            await self._client.subscribe(topic)

    def register_handler_sync(self, topic: str, callback):
        """
        Регистрирует обработчик из синхронного кода.
        (callback всё равно должен быть coroutine-функцией)
        """
        self._handlers[topic] = callback
