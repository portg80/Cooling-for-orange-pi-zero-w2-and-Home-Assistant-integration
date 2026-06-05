// static/js/visualization/blobWaveVisualizer.js
class BlobWaveVisualizer {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext('2d');
        this.audioData = new Array(512).fill(0);
        this.smoothData = new Array(512).fill(0);
        this.currentState = 'unmuted';
        this.isCommandActive = false;

        this.config = {
            baseRadius: 80, // Базовый радиус круга
            amplitude: 0.5, // Амплитуда волн (0-1)
            smoothing: 0.8, // Сглаживание анимации
            detail: 35, // Количество точек для создания круга
            lineWidth: 5,
            chaos: 0.5, // Уровень хаотичности
            glowStrength: 15,

            // Цвета — вынесены в настройки
            strokeStartColor: '#C7C7C7',
            strokeEndColor: '#FFFFFF',
            fillStartColor: '#F6F6F6',
            fillEndColor: '#E4EAED',
            fillAlpha: 1 // Альфа для заливки (0..1)
        };

        this._setupCanvas();
        this.startAnimation();
    }

    _setupCanvas() {
        const resizeCanvas = () => {
            this.canvas.width = this.canvas.clientWidth;
            this.canvas.height = this.canvas.clientHeight;
            // Пересчитываем базовый радиус относительно размера canvas
            this.config.baseRadius = Math.min(this.canvas.width, this.canvas.height) * 0.35;
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

    // Возвращает объект {r,g,b} — удобно для rgba и rgb
    _lerpColorComponents(a, b, t) {
        const as = a.trim().replace(/#/g, '');
        const bs = b.trim().replace(/#/g, '');
        const ah = parseInt(as, 16);
        const bh = parseInt(bs, 16);
        const ar = (ah >> 16) & 0xff, ag = (ah >> 8) & 0xff, ab = ah & 0xff;
        const br = (bh >> 16) & 0xff, bg = (bh >> 8) & 0xff, bb = bh & 0xff;
        const rr = Math.round(ar + t * (br - ar));
        const rg = Math.round(ag + t * (bg - ag));
        const rb = Math.round(ab + t * (bb - ab));
        return { r: rr, g: rg, b: rb };
    }

    _rgbToString(c) {
        return `rgb(${c.r},${c.g},${c.b})`;
    }

    _rgbaToString(c, a) {
        return `rgba(${c.r},${c.g},${c.b},${a})`;
    }

    draw() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

        const centerX = this.canvas.width / 2;
        const centerY = this.canvas.height / 2;

        // Сглаживание данных
        for (let i = 0; i < this.audioData.length; i++) {
            this.smoothData[i] = this.smoothData[i] * this.config.smoothing +
                                this.audioData[i] * (1 - this.config.smoothing);
        }

        // Вычисляем интенсивность звука
        const rms = Math.sqrt(this.smoothData.reduce((s, v) => s + v * v, 0) / this.smoothData.length);
        const intensity = Math.min(1, rms * 10);

        // Получаем цвета из настроек config (если захотите, можно сделать fallback к CSS-переменным)
        const strokeStart = this.config.strokeStartColor || '#C7C7C7';
        const strokeEnd = this.config.strokeEndColor || '#FFFFFF';
        const fillStart = this.config.fillStartColor || strokeStart;
        const fillEnd = this.config.fillEndColor || strokeEnd;
        const fillAlpha = (typeof this.config.fillAlpha === 'number') ? this.config.fillAlpha : 0.125;

        // Линейная интерполяция цветов по интенсивности
        const strokeComp = this._lerpColorComponents(strokeStart, strokeEnd, intensity);
        const fillComp = this._lerpColorComponents(fillStart, fillEnd, intensity);

        const strokeColorRgb = this._rgbToString(strokeComp);
        const fillColorRgba = this._rgbaToString(fillComp, fillAlpha);

        // Создаем blob-фигуру
        this.ctx.beginPath();

        for (let i = 0; i <= this.config.detail; i++) {
            const baseAngle = (i / this.config.detail) * Math.PI * 2;
            const angle = baseAngle + (Math.random() - 0.5) * 0.05; // смещение ±0.01π

            const audioIndex = Math.floor(i * this.audioData.length / this.config.detail) % this.audioData.length;

            // Синусное окно для плавного замыкания
            const windowFactor = Math.sin(angle);

            const audioInfluence = this.smoothData[audioIndex] * this.config.amplitude * windowFactor;

            // Симметричный chaos
            const chaos = Math.sin(angle * 7 + Date.now() * 0.001) * this.config.chaos * Math.pow(windowFactor, 1.5);


            // Используем синус/косинус и смещение по времени для органичного движения
            const time = Date.now() * 0.0005; // медленное движение волн
            const waveNoise = noise.perlin3(Math.cos(angle), Math.sin(angle), time) * 0.1;

            const audioWave = this.smoothData[audioIndex] * this.config.amplitude * 0.5; // влияние звука

            // Итоговый радиус
            const radius = this.config.baseRadius * (1 + waveNoise + audioWave + intensity * 0.2);

            const x = centerX + Math.cos(angle) * radius;
            const y = centerY + Math.sin(angle) * radius;

            if (i === 0) this.ctx.moveTo(x, y);
            else this.ctx.lineTo(x, y);
        }
        this.ctx.closePath();

        // Стили с эффектом свечения
        this.ctx.fillStyle = fillColorRgba; // Полупрозрачная заливка из config
        this.ctx.strokeStyle = strokeColorRgb;
        this.ctx.lineWidth = this.config.lineWidth;
        this.ctx.shadowBlur = this.config.glowStrength;
        this.ctx.shadowColor = strokeColorRgb;

        this.ctx.fill();
        this.ctx.stroke();

        // Сбрасываем тень для следующих отрисовок
        this.ctx.shadowBlur = 0;
    }

    startAnimation() {
        const animate = () => {
            this.draw();
            requestAnimationFrame(animate);
        };
        animate();
    }
}
