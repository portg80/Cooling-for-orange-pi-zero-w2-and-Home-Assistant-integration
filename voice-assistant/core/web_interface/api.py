

"""Я написал голосового ассистента. Модуль WakeWord в нем отвечает за пробуждение ассистента и "передачу" управления уже тяжёлой модели распознавания STT Vosk.
Я постарался к WakeWord сделать апи запросы с помощью которых пользователь через фронтенд сможет "замутить" микрофон и наоборот (/api/voicecore/wakeword/*).

/api/voicecore/assistant/* уже отвечает за управление голосовой моделью STT Vosk.
Например, activate-listening-command позволит по кнопке вызвать ассистента для прослушивания команды (в обход WakeWord, те без произношения триггер слова).


Дело в том, что я переделывал названия АПИ и функции которые они используют для ясности что за что отвечает и какую функцию выполняет.
твоя задача проверить..."""
from flask import jsonify, request

class AssistantAPI:
    """REST API для управления ассистентом"""

    def __init__(self, assistant):
        self.assistant = assistant

    def register_routes(self, app):
        """Регистрация API маршрутов"""

        @app.route('/api/voicecore/status-voice-engine', methods=['GET'])
        def get_status_voice_engine():
            """Получение статусов ассистента"""
            return jsonify({
                'state_assistant_vosk': self.assistant.state_assistant_vosk,
                'wakeword_paused': self.assistant.wakeword_engine.is_paused()
            })

        @app.route('/api/voicecore/assistant/activate-listening-command', methods=['POST'])
        def assistant_activate_listening_command():
            """Принудительная активация ассистента.
            Позволяет по кнопке вызвать ассистента
            для прослушивания команды (в обход WakeWord,
            те без произношения триггер слова)."""
            try:
                self.assistant.activate_listening_command()
                return jsonify({'status': 'activated', 'message': 'Ассистент активирован'})
            except Exception as e:
                return jsonify({'status': 'error', 'message': str(e)}), 500

        @app.route('/api/voicecore/assistant/cancel-listening-command', methods=['POST'])
        def assistant_cancel_listening_command():
            """останавливает прослушивание команды в vosk,
            тоесть если пользователь говорил, но передумал
            выполнять команду то сможет "отчистить" то
            что там наговорил и это не передастся клиенту"""
            try:
                self.assistant.cancel_listening_command()
                return jsonify({'status': 'cancelled', 'message': 'Команда отменена'})
            except Exception as e:
                return jsonify({'status': 'error', 'message': str(e)}), 500


        @app.route('/api/voicecore/assistant/send-text-command', methods=['POST'])
        def assistant_send_text_command():
            """Отправка текстовой команды на выполнение ассистенту.
            в обход произношения триггер слова"""
            try:
                data = request.get_json()
                text = data.get('text', '')

                if text:
                    # Эмулируем голосовую команду через текстовый ввод
                    cmd, converted_text = self.assistant.nlu.best_match(text)
                    if cmd:
                        cmd.execute(text, converted_text)
                        return jsonify({'status': 'executed', 'message': f'Команда выполнена: {text}'})
                    else:
                        return jsonify({'status': 'not_found', 'message': 'Команда не распознана'})
                else:
                    return jsonify({'status': 'error', 'message': 'Текст команды не указан'}), 400

            except Exception as e:
                return jsonify({'status': 'error', 'message': str(e)}), 500


        @app.route('/api/voicecore/wakeword/status', methods=['GET'])
        def get_wakeword_status():
            """Получение статуса wakeword"""
            if hasattr(self.assistant, 'get_wakeword_status'):
                status = self.assistant.get_wakeword_status()
                return jsonify(status)
            return jsonify({'status': 'error', 'message': 'Wakeword status unavailable'}), 500

        @app.route('/api/voicecore/wakeword/toggle-mute', methods=['POST'])
        def wakeword_toggle_mute():
            """Переключение состояния wakeword. мут/анмут микрофона"""
            try:
                if not hasattr(self.assistant, 'wakeword_toggle_mute'):
                    return jsonify({
                        'status': 'error',
                        'message': 'Переключение wakeword not available'
                    }), 501

                success = self.assistant.wakeword_toggle_mute()

                if not success:
                    return jsonify({
                        'status': 'error',
                        'message': 'Не удалось переключить wakeword'
                    }), 500

                status = self.assistant.get_wakeword_status()
                wakeword_active = status.get('wakeword_active', False)
                manual_mute = status.get('manual_mute', False)

                if wakeword_active and not manual_mute:
                    message = "Wakeword включён"

                else:
                    message = "Wakeword отключен"


                return jsonify({
                    'status': 'success',
                    'message': message,
                    'state_assistant_vosk': self.assistant.state_assistant_vosk,
                    'wakeword_active': wakeword_active,
                    'manual_mute': manual_mute
                })

            except Exception as e:
                return jsonify({'status': 'error', 'message': str(e)}), 500

        @app.route('/api/voicecore/wakeword/mute', methods=['POST'])
        def wakeword_mute():
            """Отключение wakeword. Мут микрофона"""
            try:
                if hasattr(self.assistant, 'wakeword_mute'):
                    success = self.assistant.wakeword_mute()
                    if success:
                        return jsonify({
                            'status': 'success',
                            'message': 'Wakeword замучен',
                            'wakeword_state': 'muted'
                        })
                    else:
                        return jsonify({'status': 'error', 'message': 'Failed to mute wakeword'}), 500
                else:
                    return jsonify({'status': 'error', 'message': 'Mute wakeword not available'}), 500
            except Exception as e:
                return jsonify({'status': 'error', 'message': str(e)}), 500

        @app.route('/api/voicecore/wakeword/unmute', methods=['POST'])
        def wakeword_unmute():
            """Включение wakeword. Анмут микрофона"""
            try:
                if hasattr(self.assistant, 'wakeword_unmute'):
                    success = self.assistant.wakeword_unmute()
                    if success:
                        return jsonify({
                            'status': 'success',
                            'message': 'Wakeword включен',
                            'wakeword_state': 'listening'
                        })
                    else:
                        return jsonify({'status': 'error', 'message': 'Failed to unmute wakeword'}), 500
                else:
                    return jsonify({'status': 'error', 'message': 'Unmute wakeword not available'}), 500
            except Exception as e:
                return jsonify({'status': 'error', 'message': str(e)}), 500

        @app.route('/api/avatar/apply-skin', methods=['POST'])
        def apply_skin():
            """Применение скина"""
            try:
                data = request.get_json()
                skin_name = data.get('skin', 'default')

                # Здесь можно добавить логику применения скинов на сервере
                # и broadcast через WebSocket для синхронизации между клиентами

                return jsonify({'status': 'success', 'message': f'Скин {skin_name} применен', 'skin': skin_name})
            except Exception as e:
                return jsonify({'status': 'error', 'message': str(e)}), 500
