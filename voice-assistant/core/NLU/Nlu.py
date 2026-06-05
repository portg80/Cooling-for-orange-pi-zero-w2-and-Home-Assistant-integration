# core/NLU/nlu.py
from difflib import SequenceMatcher
from core.NLU.number_converter import NumberConverter
from commands.Base_command import BaseCommand
from typing import Optional, Tuple, Union


class NLU:
    def __init__(self, commands):
        self.commands = commands
        self.number_converter = NumberConverter()

    def best_match(self, text) -> Tuple[Optional[BaseCommand], str]:
        # Convert number words to numerals before matching
        converted_text, was_converted = self.number_converter.convert_words_to_numbers(text)
        if was_converted:
            print(f"Original text: {text}")
            print(f"Converted text: {converted_text}")

        # Сначала ищем команды с match_type = "exact" и "contains"
        for cmd in self.commands:
            if cmd.match_type in ["exact", "contains", "keyword"]:
                if cmd.match(converted_text):
                    return cmd, converted_text

        # Если не нашли, используем fuzzy matching для остальных команд
        best = None
        best_score = 0
        for cmd in self.commands:
            if cmd.match_type == "fuzzy":
                for alias in cmd.aliases:
                    score = SequenceMatcher(None, alias, converted_text).ratio()
                    if score > best_score and score > 0.6:
                        best_score = score
                        best = cmd

        return (best, converted_text) if best else (None, converted_text)
