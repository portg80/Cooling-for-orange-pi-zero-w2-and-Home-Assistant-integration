// static/js/handlers/eventHandlers.js
class EventHandlers {
    constructor(apiClient, chatManager, stateManager, skinManager) {  // ДОБАВЬТЕ skinManager в параметры
        this.apiClient = apiClient;
        this.chatManager = chatManager;
        this.stateManager = stateManager;
        this.skinManager = skinManager; // Теперь skinManager определен
        this.isAssistantActive = false;
        this._bindEvents();
    }


    _bindEvents() {
        // Кнопки управления
        document.getElementById('sendTextBtn').addEventListener('click', () => this.handleSendText());
        document.getElementById('textCommand').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.handleSendText();
        });

        // Обработчик клика по круглой кнопке с волной
        document.getElementById('wave-button').addEventListener('click', () => this.handleWaveButtonClick());

        // Управление прослушиванием
        document.getElementById('toggleListeningBtn').addEventListener('click', () => this.handleToggleListening());
    }

    async handleSendText() {
        const textInput = document.getElementById('textCommand');
        const text = textInput.value.trim();

        if (text) {
            try {
                // Добавляем сообщение пользователя в чат
                this.chatManager.addMessage(text, 'recognized_speech');

                const data = await this.apiClient.sendTextCommand(text);
                this.chatManager.addMessage(data.message, 'info');
                textInput.value = '';
                this.stateManager.setCommandRecognitionState(true);

                setTimeout(() => {
                    this.stateManager.setCommandRecognitionState(false);
                }, 3000);
            } catch (error) {
                this.chatManager.addMessage('Ошибка отправки команды: ' + error.message, 'error');
                this.stateManager.waveVisualizer.setState('error');
            }
        }
    }

    async handleActivate() {
        try {
            const data = await this.apiClient.activateAssistant();
            this.chatManager.addMessage(data.message, 'info');
            this.stateManager.setCommandRecognitionState(true);
        } catch (error) {
            this.stateManager.waveVisualizer.setState('error');
        }
    }

    async handleCancel() {
        try {
            const data = await this.apiClient.cancelCommand();
            this.chatManager.addMessage(data.message, 'info');
            this.stateManager.setCommandRecognitionState(false);
        } catch (error) {
            this.stateManager.waveVisualizer.setState('error');
        }
    }


    async handleWaveButtonClick() {
        try {
            if (!this.isAssistantActive) {
                // Активируем ассистента - ТОЛЬКО API и UI, без визуализатора
                const data = await this.apiClient.activateAssistant();
                this.chatManager.addMessage(data.message, 'info');
                this.isAssistantActive = true;
                this.updateWaveButtonState(true);
            } else {
                // Отменяем команду - ТОЛЬКО API и UI, без визуализатора
                const data = await this.apiClient.cancelCommand();
                this.chatManager.addMessage(data.message, 'info');
                this.isAssistantActive = false;
                this.updateWaveButtonState(false);
            }
        } catch (error) {
            console.error('Error toggling assistant:', error);
            this.chatManager.addMessage('Ошибка переключения ассистента: ' + error.message, 'error');
            // НЕ ВЫЗЫВАЕМ ВИЗУАЛИЗАТОР - он не имеет отношения к переключению ассистента
        }
    }

    updateWaveButtonState(isActive) {
        const waveButton = document.getElementById('wave-button');
        const waveContainer = document.getElementById('wave-container');

        if (!waveButton || !waveContainer) {
            console.error('Wave button or container not found');
            return;
        }

        const waveIcon = waveButton.querySelector('.wave-icon');
        if (!waveIcon) {
            console.error('Wave icon not found');
            return;
        }

        if (isActive) {
            // Состояние "активно" - красный цвет для отмены
            waveButton.classList.remove('wave-state-unmuted');
            waveButton.classList.add('wave-state-command');
            waveContainer.classList.remove('wave-state-unmuted');
            waveContainer.classList.add('wave-state-command');
            waveIcon.className = 'bi bi-x-lg wave-icon'; // иконка крестика
        } else {
            // Состояние "неактивно" - обычный цвет
            waveButton.classList.remove('wave-state-command');
            waveButton.classList.add('wave-state-unmuted');
            waveContainer.classList.remove('wave-state-command');
            waveContainer.classList.add('wave-state-unmuted');
            waveIcon.className = 'bi bi-mic-fill wave-icon'; // иконка микрофона
        }
    }


    async handleToggleListening() {
        try {
            // Получаем статус ассистента
            const status = await this.apiClient.getStatus();
            const isAssistantActive = status.state !== 'IDLE';

            // Если ассистент активен, сначала отменяем команду
            if (isAssistantActive) {
                await this.apiClient.cancelCommand();
                this.chatManager.addMessage('Текущая команда остановлена перед отключением микрофона', 'info');
            }

            // Теперь переключаем состояние прослушивания
            const data = await this.apiClient.toggleListening();
            if (data.status === 'success') {
                this.chatManager.addMessage(data.message, 'info');
                setTimeout(() => this.stateManager.updateWaveStateFromStatus(), 100);
            } else {
                this.chatManager.addMessage('Ошибка: ' + data.message, 'error');
                this.stateManager.waveVisualizer.setState('error');
            }
        } catch (error) {
            console.error('Error toggling listening:', error);
            this.chatManager.addMessage('Ошибка при переключении прослушивания', 'error');
            this.stateManager.waveVisualizer.setState('error');
        }
    }

}
