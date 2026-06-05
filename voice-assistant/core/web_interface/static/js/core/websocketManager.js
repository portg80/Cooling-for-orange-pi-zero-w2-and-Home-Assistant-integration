// static/js/core/websocketManager.js
class WebSocketManager {
    constructor() {
        this.audioWs = new WebSocket(`ws://${window.location.host}/ws/audio`);
        this.textWs = new WebSocket(`ws://${window.location.host}/ws/text`);
        this.audioData = new Array(512).fill(0);
        this.textMessageCallbacks = [];
        this.audioDataCallbacks = [];

        this._setupEventHandlers();
    }

    _setupEventHandlers() {
        this.audioWs.onmessage = (event) => {
            this.audioData = JSON.parse(event.data);
            this.audioDataCallbacks.forEach(callback => callback(this.audioData));
        };

        this.textWs.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.textMessageCallbacks.forEach(callback => callback(data));
        };
    }

    onAudioData(callback) {
        this.audioDataCallbacks.push(callback);
    }

    onTextMessage(callback) {
        this.textMessageCallbacks.push(callback);
    }

    getAudioData() {
        return this.audioData;
    }
}
