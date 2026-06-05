// static/js/core/apiClient.js
class ApiClient {
    constructor() {
        this.baseUrl = '';
    }

    async _fetch(endpoint, options = {}) {
        try {
            const response = await fetch(`/api${endpoint}`, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error(`API request failed: ${error}`);
            throw error;
        }
    }

    async getStatus() {
        return await this._fetch('/status');
    }

    async activateAssistant() {
        return await this._fetch('/activate', { method: 'POST' });
    }

    async cancelCommand() {
        return await this._fetch('/cancel', { method: 'POST' });
    }

    async toggleWakeWord() {
        return await this._fetch('/toggle-wakeword', { method: 'POST' });
    }

    async sendTextCommand(text) {
        return await this._fetch('/send-text', {
            method: 'POST',
            body: JSON.stringify({ text })
        });
    }

    async getListeningStatus() {
        return await this._fetch('/listening-status');
    }

    async toggleListening() {
        return await this._fetch('/toggle-listening', { method: 'POST' });
    }

    async muteListening() {
        return await this._fetch('/mute-listening', { method: 'POST' });
    }

    async unmuteListening() {
        return await this._fetch('/unmute-listening', { method: 'POST' });
    }
}
