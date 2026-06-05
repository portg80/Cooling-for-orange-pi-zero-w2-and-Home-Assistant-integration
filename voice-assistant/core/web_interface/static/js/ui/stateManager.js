// static/js/ui/stateManager.js
class StateManager {
    constructor(apiClient, waveVisualizer) {
        this.apiClient = apiClient;
        this.waveVisualizer = waveVisualizer;
        this.isCommandActive = false;
    }

    async updateStatus() {
        try {
            const data = await this.apiClient.getStatus();
            document.getElementById('activeStatus').textContent = data.active ? 'да' : 'нет';
            document.getElementById('stateStatus').textContent = data.state;
            document.getElementById('wakewordStatus').textContent =
                data.wake_word_paused ? 'приостановлен' : 'активен';

            // Синхронизируем состояние с кнопкой
            if (data.active && !this.isCommandActive) {
                this.setCommandRecognitionState(true);
                // Обновляем состояние в eventHandlers если нужно
                if (window.app && window.app.eventHandlers) {
                    window.app.eventHandlers.isAssistantActive = true;
                    window.app.eventHandlers.updateWaveButtonState(true);
                }
            } else if (!data.active && this.isCommandActive) {
                this.setCommandRecognitionState(false);
                if (window.app && window.app.eventHandlers) {
                    window.app.eventHandlers.isAssistantActive = false;
                    window.app.eventHandlers.updateWaveButtonState(false);
                }
            }
        } catch (error) {
            console.error('Error updating status:', error);
        }
    }

    // УДАЛЯЕМ этот метод или делаем его пустым
    setCommandRecognitionState(isActive) {
        this.isCommandActive = isActive;
        // НИЧЕГО НЕ ДЕЛАЕМ - переключение ассистента не должно влиять на визуализатор
    }

    startPeriodicUpdates() {
        setInterval(() => this.updateListeningStatus(), 3000);
        setInterval(() => this.updateStatus(), 2000);
        setInterval(() => {
            if (!this.isCommandActive) {
                this.updateWaveStateFromStatus();
            }
        }, 2000);
    }

   async updateWaveStateFromStatus() {
        if (this.isCommandActive) return;

        try {
            const data = await this.apiClient.getListeningStatus();
            if (data.manual_mute || !data.wakeword_active) {
                this.waveVisualizer.setState('muted');
            } else {
                this.waveVisualizer.setState('unmuted');
            }
        } catch (error) {
            this.waveVisualizer.setState('error');
        }
    }
}
