# core/Command_manager.py
import importlib
import pkgutil
from commands.Base_command import BaseCommand
from core.NLU.number_converter import NumberConverter
from typing import Optional

class CommandManager:
    def __init__(self, assistant=None, sound_player=None):
        self.commands = []
        self.assistant = assistant
        self.sound_player = sound_player
        self.number_converter = NumberConverter()
        self._load_commands()

    def _load_commands(self):
        import commands
        for loader, name, ispkg in pkgutil.iter_modules(commands.__path__):
            module = importlib.import_module(f"commands.{name}")
            for obj in module.__dict__.values():
                if isinstance(obj, type) and issubclass(obj, BaseCommand) and obj is not BaseCommand:
                    try:
                        command_instance = obj(
                            assistant=self.assistant,
                            sound_player=self.sound_player
                        )
                    except TypeError:
                        print(f"⚠ Команда {obj.__name__} не поддерживает параметры, создаем без них")
                        command_instance = obj()

                    self.commands.append(command_instance)
                    print(f"✅ Загружена команда: {command_instance.name} (тип: {command_instance.match_type})")

    def find_command(self, text: str) -> Optional[BaseCommand]:
        """Находит команду по тексту (использует встроенный matching команд)"""
        for cmd in self.commands:
            if cmd.match(text):
                return cmd
        return None
