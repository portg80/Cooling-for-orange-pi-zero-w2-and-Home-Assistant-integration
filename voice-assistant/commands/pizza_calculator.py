# commands/Pizza_calculator.py
import math
import re
import random
from .Base_command import BaseCommand


class PizzaCalculatorCommand(BaseCommand):
    name = "расчет пиццы"
    aliases = [
        "расчет пиццы",
        "рассчитай пиццу",
        "посчитай пиццу"
    ]
    keywords = [
        "пицц",
        "рассчитай",
        "посчитай",
        "калькулятор пиццы",
        "цена пиццы",
        "стоимость пиццы",
        "выгодная пицца",
        "площадь пиццы"
    ]
    match_type = "keyword"  # Используем поиск по ключевым словам

    def __init__(self, assistant=None, sound_player=None):
        super().__init__(assistant, sound_player)

    def execute(self, text: str, converted_text: str = None, *args, **kwargs):
        try:
            # Используем конвертированный текст если есть, иначе оригинальный
            processing_text = converted_text if converted_text else text

            print(f"[PIZZA] Обрабатываем запрос: {processing_text}")

            # Извлекаем параметры
            diameter, radius, price = self._extract_parameters(processing_text)

            # Проверяем, что есть достаточно данных
            if diameter is None and radius is None:
                self.say("Пожалуйста, укажите диаметр или радиус пиццы. Например: 'пицца диаметром 30 сантиметров'")
                return

            if price is None:
                self.say("Пожалуйста, укажите цену пиццы. Например: 'за 500 рублей'")
                return

            # Вычисляем площадь
            if diameter is not None:
                area = self._calculate_area_from_diameter(diameter)
                size_info = f"диаметром {diameter} см"
            else:
                area = self._calculate_area_from_radius(radius)
                size_info = f"радиусом {radius} см"

            # Вычисляем цену за кв. см
            price_per_cm2 = price / area

            # Формируем ответ
            response = self._format_response(size_info, area, price, price_per_cm2)

            self.say(response)
            print(f"[PIZZA] {response}")

            # Воспроизводим звук успешного расчета
            self.play_random_sound("calculations", "success", "click", volume=0.3)

        except Exception as e:
            error_msg = "Извините, произошла ошибка при расчете пиццы. Попробуйте еще раз."
            self.say(error_msg)
            print(f"[PIZZA] Ошибка: {e}")

    def _extract_parameters(self, text: str):
        """Извлекает диаметр, радиус и цену из текста"""
        text_lower = text.lower()

        # Ищем все числа в тексте
        numbers = re.findall(r'\d+[.,]?\d*', text_lower)
        numbers = [float(num.replace(',', '.')) for num in numbers]

        diameter = None
        radius = None
        price = None

        # Ищем диаметр
        diameter_match = re.search(r'диаметр\w*\s*(\d+[.,]?\d*)', text_lower)
        if diameter_match:
            diameter = float(diameter_match.group(1).replace(',', '.'))
        else:
            # Ищем упоминание диаметра в другом формате
            diam_phrases = ['см пицц', 'сантиметр пицц', 'диаметр']
            if any(phrase in text_lower for phrase in diam_phrases) and numbers:
                diameter = numbers[0]

        # Ищем радиус
        radius_match = re.search(r'радиус\w*\s*(\d+[.,]?\d*)', text_lower)
        if radius_match:
            radius = float(radius_match.group(1).replace(',', '.'))

        # Ищем цену
        price_match = re.search(r'(\d+[.,]?\d*)\s*(руб|р|рублей|цена|стоит|за)', text_lower)
        if price_match:
            price = float(price_match.group(1).replace(',', '.'))
        else:
            # Если цена не найдена по шаблону, берем последнее число
            if numbers:
                if diameter is not None and len(numbers) > 1:
                    price = numbers[1]
                elif radius is not None and len(numbers) > 1:
                    price = numbers[1]
                elif len(numbers) == 1 and (diameter is None and radius is None):
                    # Если только одно число и не определили размер, предполагаем что это диаметр
                    diameter = numbers[0]
                elif len(numbers) >= 2:
                    price = numbers[-1]

        return diameter, radius, price

    def _calculate_area_from_diameter(self, diameter):
        return math.pi * ((diameter / 2) ** 2)

    def _calculate_area_from_radius(self, radius):
        return math.pi * (radius ** 2)

    def _format_response(self, size_info, area, price, price_per_cm2):
        area_rounded = round(area, 2)
        price_per_cm2_rounded = round(price_per_cm2, 4)

        responses = [
            f"Пицца {size_info} имеет площадь {area_rounded} кв. см. "
            f"Цена за квадратный сантиметр: {price_per_cm2_rounded} руб.",

            f"Результат: площадь {area_rounded} см², "
            f"стоимость одного квадратного сантиметра {price_per_cm2_rounded} рублей.",

            f"Рассчитано! Площадь пиццы: {area_rounded} см². "
            f"При цене {price} рублей, за каждый см² вы платите {price_per_cm2_rounded} руб."
        ]

        return random.choice(responses)
