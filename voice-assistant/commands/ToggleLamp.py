import re
import requests
from .Base_command import BaseCommand


class ToggleLamp(BaseCommand):
    """
    Голосовое управление светом в Satisfactory через локальный FastAPI.

    Поддерживаемые фразы (примеры):
    - "включи свет 2 4"       -> лампа группы 2, номер 4 (lamp-2-4)
    - "выключи свет 6"        -> все лампы группы 6
    - "включи свет"           -> весь свет
    - "установи цвет света на красный"
    - "установи цвет света 5 3 на синий"
    - "яркость света на 20 процентов"
    """

    name = "управление светом"
    aliases = [
        "переключи лампу",
        "включи свет",
        "выключи свет",
        "переключи свет",
        "лампа",
        "свет",
        "яркость света",
        "цвет света",
    ]
    match_type = "contains"

    def __init__(
        self,
        assistant=None,
        sound_player=None,
        base_url: str = "http://127.0.0.1:8000",
    ):
        super().__init__(assistant, sound_player)
        self.base_url = base_url
        self.session = requests.Session()

    # ====== Вспомогательные HTTP ======

    def _get(self, path: str, timeout: float = 2.0) -> requests.Response | None:
        url = self.base_url + path
        try:
            print(f"[HTTP] GET {url}")
            resp = self.session.get(url, timeout=timeout)
            print(f"[HTTP] -> {resp.status_code} {resp.text!r}")
            return resp
        except requests.RequestException as e:
            print(f"[HTTP] GET ERROR {url}: {e}")
            return None

    def _post(
        self,
        path: str,
        data: str | None = None,
        timeout: float = 3.0,
        content_type: str | None = None,
    ) -> requests.Response | None:
        url = self.base_url + path
        headers = {}
        if content_type:
            headers["Content-Type"] = content_type
        try:
            print(f"[HTTP] POST {url} data={data!r}")
            resp = self.session.post(url, data=data, headers=headers, timeout=timeout)
            print(f"[HTTP] -> {resp.status_code} {resp.text!r}")
            return resp
        except requests.RequestException as e:
            print(f"[HTTP] POST ERROR {url}: {e}")
            return None

    # ====== Парсинг фразы ======

    @staticmethod
    def _extract_numbers(text: str) -> list[int]:
        return [int(x) for x in re.findall(r"\d+", text)]

    @staticmethod
    def _detect_action(text: str) -> str:
        """
        Возвращает режим:
        - "on" / "off" / "toggle"
        - "brightness" / "color"
        """
        t = text.lower()

        if "яркость" in t:
            return "brightness"
        if "цвет" in t:
            return "color"

        if "включ" in t:
            return "on"
        if "выключ" in t:
            return "off"
        if "переключ" in t:
            return "toggle"

        # по умолчанию считаем toggle
        return "toggle"

    @staticmethod
    def _detect_color_rgba(text: str) -> tuple[float, float, float, float] | None:
        """
        Дедектив цвет по словам (грубый, но рабочий парсер).
        Возвращает (r,g,b,a) в 0..1 или None.
        """
        t = text.lower()

        # Очень тупой, но практичный маппинг
        if "красн" in t:
            return (1.0, 0.0, 0.0, 1.0)
        if "зелён" in t or "зелен" in t:
            return (0.0, 1.0, 0.0, 1.0)
        if "син" in t:
            return (0.0, 0.0, 1.0, 1.0)
        if "жёлт" in t or "желт" in t:
            return (1.0, 1.0, 0.0, 1.0)
        if "фиолет" in t:
            return (0.5, 0.0, 0.5, 1.0)
        if "бел" in t:
            return (1.0, 1.0, 1.0, 1.0)
        if "оранж" in t:
            return (1.0, 0.5, 0.0, 1.0)

        return None

    @staticmethod
    def _extract_percentage(text: str) -> int | None:
        """
        Ищем число перед словом "процент"/"процентов" или любое число в фразе.
        Возвращаем 0..100 или None.
        """
        t = text.lower()
        # сначала пробуем паттерн "на 20 процентов"
        m = re.search(r"(\d+)\s*процент", t)
        if m:
            return max(0, min(100, int(m.group(1))))

        nums = [int(x) for x in re.findall(r"\d+", t)]
        if nums:
            return max(0, min(100, nums[0]))

        return None

    # ====== Логика включения/выключения через toggle + GET ======

    def _ensure_state(self, scope: str, group: int | None, index: int | None, desired: str):
        """
        scope: "all"|"group"|"lamp"
        desired: "on"/"off"
        Использует GET, чтобы узнать текущее состояние, и дергает toggle только если нужно.
        """
        assert desired in ("on", "off")

        # Определяем путь GET для проверки
        if scope == "lamp":
            assert group is not None and index is not None
            resp = self._get(f"/lamp/{group}/{index}")
        elif scope == "group":
            assert group is not None
            # для группы отдельного GET нет — можно чекать любую лампу группы
            # но проще ориентироваться на global, а затем просто вызывать toggle:
            # чтобы не усложнять, просто вызываем toggle один раз -> "семантика" on/off не 100%, но ок.
            # если хочется идеального поведения — нужно расширять API.
            resp = None
        else:  # "all"
            resp = self._get("/lamp")

        # Если нет GET или нет ответа — просто дергаем toggle, чтобы не зависнуть
        if resp is None or not resp.ok:
            self._call_toggle(scope, group, index)
            return

        current = resp.text.strip().lower()
        if current not in ("on", "off"):
            self._call_toggle(scope, group, index)
            return

        if current == desired:
            print(f"[LOGIC] Уже {desired}, toggle не нужен (scope={scope}, group={group}, index={index})")
            return

        # иначе меняем
        self._call_toggle(scope, group, index)

    def _call_toggle(self, scope: str, group: int | None, index: int | None):
        if scope == "lamp":
            path = f"/lamp/toggle/{group}/{index}"
        elif scope == "group":
            path = f"/lamp/toggle/{group}"
        else:
            path = "/lamp/toggle"

        self._post(path)

    # ====== Обработка разных режимов ======

    def _handle_switch(self, phrase: str, action: str):
        """
        Включить/выключить/переключить свет.
        """
        nums = self._extract_numbers(phrase)
        if len(nums) >= 2:
            group, index = nums[0], nums[1]
            scope = "lamp"
            target_msg = f"светильник {group} {index}"
        elif len(nums) == 1:
            group, index = nums[0], None
            scope = "group"
            target_msg = f"группу света {group}"
        else:
            group = index = None
            scope = "all"
            target_msg = "весь свет"

        # Озвучка
        if action == "on":
            self.say(f"Включаю {target_msg}.")
        elif action == "off":
            self.say(f"Выключаю {target_msg}.")
        else:
            self.say(f"Переключаю {target_msg}.")

        # Логика
        if action in ("on", "off"):
            self._ensure_state(scope, group, index, action)
        else:
            self._call_toggle(scope, group, index)

        self.say("Готово.")

    def _handle_brightness(self, phrase: str):
        percent = self._extract_percentage(phrase)
        if percent is None:
            self.say("Не поняла уровень яркости.")
            return

        value = max(0.0, min(1.0, percent / 100.0))
        self.say(f"Устанавливаю яркость света на {percent} процентов.")
        resp = self._post("/panel/intensity", data=str(value), content_type="text/plain")
        if not resp or not resp.ok:
            self.say("Не удалось изменить яркость света.")
        else:
            self.say("Яркость установлена.")

    def _handle_color(self, phrase: str):
        rgba = self._detect_color_rgba(phrase)
        if rgba is None:
            self.say("Не поняла, какой цвет установить.")
            return

        r, g, b, a = rgba
        payload = f"{r},{g},{b},{a}"
        # Пока API меняет цвет глобально для всех ламп.
        # Если нужно менять по группам/лампам — надо расширять backend.
        self.say("Устанавливаю цвет света.")
        resp = self._post("/panel/color", data=payload, content_type="text/plain")
        if not resp or not resp.ok:
            self.say("Не удалось изменить цвет света.")
        else:
            self.say("Цвет установлен.")

    # ====== Входная точка команды ======

    def execute(self, text: str, converted_text: str = None, *args, **kwargs):
        phrase = (converted_text or text or "").lower()
        print(f"[CMD] Фраза ассистента: {phrase!r}")

        mode = self._detect_action(phrase)
        print(f"[CMD] Режим: {mode}")

        try:
            if mode in ("on", "off", "toggle"):
                self._handle_switch(phrase, mode)
            elif mode == "brightness":
                self._handle_brightness(phrase)
            elif mode == "color":
                self._handle_color(phrase)
            else:
                self.say("Не поняла, что сделать со светом.")
        except Exception as e:
            # чтобы ассистент не падал на исключениях
            print(f"[CMD] ERROR: {e}")
            self.say("Произошла ошибка при управлении светом.")
