// static/js/app.js
class VoiceAssistantApp {
    constructor() {
        this.apiClient = new ApiClient();
        this.websocketManager = new WebSocketManager();
        this.waveVisualizer = new BlobWaveVisualizer('wave');
        this.chatManager = new ChatManager('chatContainer', this.apiClient);
        this.stateManager = new StateManager(this.apiClient, this.waveVisualizer);

        // Сначала создаем все основные компоненты, потом skinManager
        this.skinManager = new SkinManager('skin-canvas');

        // Теперь передаем skinManager в eventHandlers
        this.eventHandlers = new EventHandlers(
            this.apiClient,
            this.chatManager,
            this.stateManager,
            this.skinManager  // передаем после создания
        );

        window.app = this;
        this._initialize();
    }

    _initialize() {
        this.websocketManager.onAudioData((audioData) => {
            this.waveVisualizer.updateAudioData(audioData);
        });

        this.websocketManager.onTextMessage((data) => {
            this.chatManager.addMessage(data.text, data.type);
            this._applySkinByPhrase(data.text);  // вызываем метод
        });

        // Загружаем сохраненный скин
        this.skinManager.loadSavedSkin();

        // Инициализация состояния
        this.stateManager.updateWaveStateFromStatus();
        this.stateManager.updateListeningStatus();
        this.stateManager.updateStatus();
        this.stateManager.startPeriodicUpdates();

        // Приветственное сообщение
        this.chatManager.addMessage('Ассистент запущен и готов к работе!', 'info');

        // Сохраняем ссылку на chatManager для глобального доступа (если нужно)
        window.chatManager = this.chatManager;
    }

    _applySkinByPhrase(text) {
        const lowerText = text.toLowerCase();

        if (lowerText.includes('очки') || lowerText.includes('glasses')) {
            this.skinManager.applySkin('glasses');
        } else if (lowerText.includes('глаз') || lowerText.includes('eyes')) {
            this.skinManager.applySkin('eyes');
        } else if (lowerText.includes('робот') || lowerText.includes('robot')) {
            this.skinManager.applySkin('robot');
        }
    }
}

// Запуск приложения после загрузки DOM
document.addEventListener('DOMContentLoaded', () => {
    new VoiceAssistantApp();
});
