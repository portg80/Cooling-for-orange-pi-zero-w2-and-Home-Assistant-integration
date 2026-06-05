// static/js/visualization/waveVisualizer.js
class WaveVisualizer {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext('2d');
        this.audioData = new Array(512).fill(0);
        this.smoothData = new Array(512).fill(0);
        this.currentState = 'unmuted';
        this.isCommandActive = false;

        this.config = {
            lineWidth: 4.5,
            amplitude: 0.6,
            smoothing: 0.9,
            glowStrength: 9
        };

        this._setupCanvas();
        this.startAnimation();
    }

    _setupCanvas() {
        const resizeCanvas = () => {
            this.canvas.width = this.canvas.clientWidth;
            this.canvas.height = this.canvas.clientHeight;
        };

        resizeCanvas();
        window.addEventListener('resize', resizeCanvas);
    }

    updateAudioData(newData) {
        this.audioData = newData;
    }

    setState(state) {
        if (this.isCommandActive && state !== 'command' && state !== 'error') {
            return;
        }

        const waveContainer = document.getElementById('wave-container');
        const waveStateIndicator = document.getElementById('waveStateIndicator');
        const waveStateDescription = document.getElementById('waveStateDescription');

        // Удаляем предыдущие классы состояний
        waveContainer.classList.remove(
            'wave-state-listening', 'wave-state-muted', 'wave-state-unmuted',
            'wave-state-command', 'wave-state-error'
        );

        // Добавляем новый класс состояния
        waveContainer.classList.add(`wave-state-${state}`);
        this.currentState = state;

        // Обновляем текстовые индикаторы
        const stateConfig = {
            'listening': { indicator: '(микрофон активен)', description: 'Микрофон активен: светло-белые тона' },
            'muted': { indicator: '(микрофон отключен)', description: 'Микрофон отключен: серые тона' },
            'unmuted': { indicator: '(микрофон активен)', description: 'Микрофон активен: светло-белые тона' },
            'command': { indicator: '(распознавание команды)', description: 'Распознавание команды: зеленые тона' },
            'error': { indicator: '(ошибка)', description: 'Ошибка: красные тона' }
        };

        const config = stateConfig[state] || stateConfig.unmuted;
        waveStateIndicator.textContent = config.indicator;
        waveStateDescription.textContent = config.description;
    }

    setCommandRecognitionState(isActive) {
        this.isCommandActive = isActive;
        if (isActive) {
            this.setState('command');
        }
    }

    _lerpColor(a, b, t) {
        const ah = parseInt(a.replace(/#/g, ''), 16);
        const bh = parseInt(b.replace(/#/g, ''), 16);
        const ar = (ah >> 16) & 0xff, ag = (ah >> 8) & 0xff, ab = ah & 0xff;
        const br = (bh >> 16) & 0xff, bg = (bh >> 8) & 0xff, bb = bh & 0xff;
        const rr = ar + t * (br - ar);
        const rg = ag + t * (bg - ag);
        const rb = ab + t * (bb - ab);
        return `rgb(${rr|0},${rg|0},${rb|0})`;
    }

    draw() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        const centerY = this.canvas.height / 2;
        const step = this.canvas.width / this.audioData.length;

        // Сглаживание
        for (let i = 0; i < this.audioData.length; i++) {
            this.smoothData[i] = this.smoothData[i] * this.config.smoothing +
                                this.audioData[i] * (1 - this.config.smoothing);
        }

        const rms = Math.sqrt(this.smoothData.reduce((s, v) => s + v * v, 0) / this.smoothData.length);
        const intensity = Math.min(1, rms * 8);

        // Получаем цвета из CSS переменных текущего состояния
        const waveContainer = document.getElementById('wave-container');
        const computedStyle = getComputedStyle(waveContainer);
        const startColor = computedStyle.getPropertyValue('--wave-start-color').trim() || '#C7C7C7';
        const endColor = computedStyle.getPropertyValue('--wave-end-color').trim() || '#FFFFFF';

        const color = this._lerpColor(startColor, endColor, intensity);

        this.ctx.beginPath();
        this.ctx.lineWidth = this.config.lineWidth;
        this.ctx.strokeStyle = color;
        this.ctx.shadowBlur = this.config.glowStrength;
        this.ctx.shadowColor = color;

        for (let i = 0; i < this.smoothData.length; i++) {
            const x = i * step;
            const y = centerY - this.smoothData[i] * (this.canvas.height * this.config.amplitude);
            if (i === 0) this.ctx.moveTo(x, y);
            else this.ctx.lineTo(x, y);
        }

        this.ctx.stroke();
    }

    startAnimation() {
        const animate = () => {
            this.draw();
            requestAnimationFrame(animate);
        };
        animate();
    }
}
