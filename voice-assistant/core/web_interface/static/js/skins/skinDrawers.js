class SkinDrawers {
    constructor(ctx, canvas) {
        this.ctx = ctx;
        this.canvas = canvas;
        this.animationTime = 0;
    }

    updateTime() {
        this.animationTime = Date.now() * 0.001;
    }

    // Скин "Очки" - исправленная версия
    drawGlasses() {
        const centerX = this.canvas.width / 2;
        const centerY = this.canvas.height / 2;

        this.ctx.strokeStyle = '#000000';
        this.ctx.lineWidth = 4;
        this.ctx.fillStyle = 'rgba(200, 200, 255, 0.2)';

        // Левый круг очков
        this.ctx.beginPath();
        this.ctx.arc(centerX - 25, centerY - 5, 20, 0, Math.PI * 2);
        this.ctx.stroke();
        this.ctx.fill();

        // Правый круг очков
        this.ctx.beginPath();
        this.ctx.arc(centerX + 25, centerY - 5, 20, 0, Math.PI * 2);
        this.ctx.stroke();
        this.ctx.fill();

        // Перемычка между очками
        this.ctx.beginPath();
        this.ctx.moveTo(centerX - 5, centerY - 5);
        this.ctx.lineTo(centerX + 5, centerY - 5);
        this.ctx.stroke();

        // Дужки очков
        this.ctx.beginPath();
        this.ctx.moveTo(centerX - 45, centerY - 5);
        this.ctx.lineTo(centerX - 60, centerY);
        this.ctx.stroke();

        this.ctx.beginPath();
        this.ctx.moveTo(centerX + 45, centerY - 5);
        this.ctx.lineTo(centerX + 60, centerY);
        this.ctx.stroke();
    }

    // Скин "Робот" с анимацией
    drawRobotEyes() {
        const centerX = this.canvas.width / 2;
        const centerY = this.canvas.height / 2;

        // Анимация пульсации
        const pulse = Math.sin(this.animationTime * 3) * 0.1 + 0.9;

        // Рисуем роботизированные глаза
        this.ctx.fillStyle = `rgba(0, 255, 136, ${0.7 * pulse})`;
        this.ctx.strokeStyle = '#ffffff';
        this.ctx.lineWidth = 2;

        // Левый глаз
        this.ctx.beginPath();
        this.ctx.arc(centerX - 30, centerY - 10, 15 * pulse, 0, Math.PI * 2);
        this.ctx.fill();
        this.ctx.stroke();

        // Правый глаз
        this.ctx.beginPath();
        this.ctx.arc(centerX + 30, centerY - 10, 15 * pulse, 0, Math.PI * 2);
        this.ctx.fill();
        this.ctx.stroke();

        // Зрачки с анимацией следования
        const pupilOffset = Math.sin(this.animationTime * 2) * 3;
        this.ctx.fillStyle = '#000000';

        this.ctx.beginPath();
        this.ctx.arc(centerX - 30 + pupilOffset, centerY - 10, 6, 0, Math.PI * 2);
        this.ctx.arc(centerX + 30 + pupilOffset, centerY - 10, 6, 0, Math.PI * 2);
        this.ctx.fill();

        // Антенна
        this.ctx.strokeStyle = '#00ff88';
        this.ctx.lineWidth = 3;
        this.ctx.beginPath();
        this.ctx.moveTo(centerX, centerY - 40);
        this.ctx.lineTo(centerX, centerY - 60);
        this.ctx.stroke();

        // Лампочка на антенне
        this.ctx.fillStyle = `hsl(${this.animationTime * 100 % 360}, 100%, 50%)`;
        this.ctx.beginPath();
        this.ctx.arc(centerX, centerY - 65, 5, 0, Math.PI * 2);
        this.ctx.fill();
    }

    // Скин "Сердце" - исправленная версия
    drawHeart() {
        const centerX = this.canvas.width / 2;
        const centerY = this.canvas.height / 2;
        const size = 15;
        const beat = Math.sin(this.animationTime * 4) * 0.1 + 1.0;

        this.ctx.fillStyle = '#ff4444';
        this.ctx.strokeStyle = '#ffffff';
        this.ctx.lineWidth = 2;

        this.ctx.save();
        this.ctx.translate(centerX, centerY);
        this.ctx.scale(beat, beat);

        this.ctx.beginPath();
        this.ctx.moveTo(0, 0 - size);

        // Рисуем левую половину сердца
        this.ctx.bezierCurveTo(
            -size * 2, 0 - size,
            -size * 2, size,
            0, size * 1.5
        );

        // Рисуем правую половину сердца
        this.ctx.bezierCurveTo(
            size * 2, size,
            size * 2, 0 - size,
            0, 0 - size
        );

        this.ctx.closePath();
        this.ctx.fill();
        this.ctx.stroke();
        this.ctx.restore();
    }

    // Скин "Звезда" - исправленная версия
    drawStar() {
        const centerX = this.canvas.width / 2;
        const centerY = this.canvas.height / 2;
        const size = 20;
        const spin = this.animationTime * 2;
        const spikes = 5;

        this.ctx.fillStyle = '#ffcc00';
        this.ctx.strokeStyle = '#ffffff';
        this.ctx.lineWidth = 2;

        this.ctx.save();
        this.ctx.translate(centerX, centerY);
        this.ctx.rotate(spin);

        this.ctx.beginPath();
        let outerRadius = size;
        let innerRadius = size * 0.4;

        for (let i = 0; i < spikes * 2; i++) {
            const radius = i % 2 === 0 ? outerRadius : innerRadius;
            const angle = (Math.PI / spikes) * i;
            const x = Math.cos(angle) * radius;
            const y = Math.sin(angle) * radius;

            if (i === 0) {
                this.ctx.moveTo(x, y);
            } else {
                this.ctx.lineTo(x, y);
            }
        }

        this.ctx.closePath();
        this.ctx.fill();
        this.ctx.stroke();
        this.ctx.restore();
    }

    // Новый скин - Кошка
    drawCat() {
        const centerX = this.canvas.width / 2;
        const centerY = this.canvas.height / 2;

        // Уши
        this.ctx.fillStyle = '#ff9966';
        this.ctx.beginPath();
        // Левое ухо
        this.ctx.moveTo(centerX - 15, centerY - 20);
        this.ctx.lineTo(centerX - 30, centerY - 40);
        this.ctx.lineTo(centerX - 10, centerY - 30);
        // Правое ухо
        this.ctx.moveTo(centerX + 15, centerY - 20);
        this.ctx.lineTo(centerX + 30, centerY - 40);
        this.ctx.lineTo(centerX + 10, centerY - 30);
        this.ctx.fill();

        // Глаза с анимацией
        const blink = Math.sin(this.animationTime * 2) > 0.5 ? 1 : 0;
        const eyeHeight = blink === 1 ? 2 : 8;

        this.ctx.fillStyle = '#66ccff';
        this.ctx.beginPath();
        this.ctx.ellipse(centerX - 15, centerY - 10, 8, eyeHeight, 0, 0, Math.PI * 2);
        this.ctx.ellipse(centerX + 15, centerY - 10, 8, eyeHeight, 0, 0, Math.PI * 2);
        this.ctx.fill();

        // Зрачки
        this.ctx.fillStyle = '#000000';
        this.ctx.beginPath();
        this.ctx.arc(centerX - 15, centerY - 10, 3, 0, Math.PI * 2);
        this.ctx.arc(centerX + 15, centerY - 10, 3, 0, Math.PI * 2);
        this.ctx.fill();

        // Нос
        this.ctx.fillStyle = '#ff6699';
        this.ctx.beginPath();
        this.ctx.moveTo(centerX, centerY);
        this.ctx.lineTo(centerX - 5, centerY + 5);
        this.ctx.lineTo(centerX + 5, centerY + 5);
        this.ctx.fill();

        // Усы
        this.ctx.strokeStyle = '#ffffff';
        this.ctx.lineWidth = 2;
        this.ctx.beginPath();
        // Левые усы
        this.ctx.moveTo(centerX - 5, centerY + 3);
        this.ctx.lineTo(centerX - 25, centerY);
        this.ctx.moveTo(centerX - 5, centerY + 5);
        this.ctx.lineTo(centerX - 25, centerY + 5);
        this.ctx.moveTo(centerX - 5, centerY + 7);
        this.ctx.lineTo(centerX - 25, centerY + 10);
        // Правые усы
        this.ctx.moveTo(centerX + 5, centerY + 3);
        this.ctx.lineTo(centerX + 25, centerY);
        this.ctx.moveTo(centerX + 5, centerY + 5);
        this.ctx.lineTo(centerX + 25, centerY + 5);
        this.ctx.moveTo(centerX + 5, centerY + 7);
        this.ctx.lineTo(centerX + 25, centerY + 10);
        this.ctx.stroke();
    }

    // Новый скин - Пришелец
    drawAlien() {
        const centerX = this.canvas.width / 2;
        const centerY = this.canvas.height / 2;
        const pulse = Math.sin(this.animationTime * 3) * 0.2 + 0.8;

        // Голова
        this.ctx.fillStyle = `rgba(0, 255, 0, ${0.7 * pulse})`;
        this.ctx.beginPath();
        this.ctx.arc(centerX, centerY - 10, 30 * pulse, 0, Math.PI * 2);
        this.ctx.fill();

        // Большие черные глаза
        this.ctx.fillStyle = '#000000';
        this.ctx.beginPath();
        this.ctx.arc(centerX - 12, centerY - 15, 8, 0, Math.PI * 2);
        this.ctx.arc(centerX + 12, centerY - 15, 8, 0, Math.PI * 2);
        this.ctx.fill();

        // Антенны
        this.ctx.strokeStyle = '#00ff00';
        this.ctx.lineWidth = 3;
        this.ctx.beginPath();
        this.ctx.moveTo(centerX - 20, centerY - 40);
        this.ctx.lineTo(centerX - 30, centerY - 60);
        this.ctx.moveTo(centerX + 20, centerY - 40);
        this.ctx.lineTo(centerX + 30, centerY - 60);
        this.ctx.stroke();

        // Лампочки на антеннах
        this.ctx.fillStyle = `hsl(${this.animationTime * 50 % 360}, 100%, 50%)`;
        this.ctx.beginPath();
        this.ctx.arc(centerX - 30, centerY - 65, 4, 0, Math.PI * 2);
        this.ctx.arc(centerX + 30, centerY - 65, 4, 0, Math.PI * 2);
        this.ctx.fill();
    }

    // ... предыдущий код ...

    // Скин "Яичница" с анимацией желтка
    drawFriedEgg() {
        const centerX = this.canvas.width / 2;
        const centerY = this.canvas.height / 2;

        // Анимация дрожания желтка
        const jiggleX = Math.sin(this.animationTime * 5) * 2;
        const jiggleY = Math.cos(this.animationTime * 4.7) * 2;

        // Белок
        //this.ctx.fillStyle = '#ffffff';
        //this.ctx.strokeStyle = '#f8f8f8';
        //this.ctx.lineWidth = 3;
        //this.ctx.beginPath();
        //this.ctx.ellipse(centerX, centerY, 40, 35, 0, 0, Math.PI * 2);
        //this.ctx.fill();
        //this.ctx.stroke();

        // Желток с анимацией
        this.ctx.fillStyle = '#ffd700';
        this.ctx.strokeStyle = '#ffaa00';
        this.ctx.lineWidth = 2;
        this.ctx.beginPath();
        this.ctx.arc(centerX + jiggleX, centerY + jiggleY, 20, 0, Math.PI * 2);
        this.ctx.fill();
        this.ctx.stroke();

        // Блики на желтке
        this.ctx.fillStyle = 'rgba(255, 255, 255, 0.6)';
        this.ctx.beginPath();
        this.ctx.arc(centerX - 5 + jiggleX, centerY - 5 + jiggleY, 5, 0, Math.PI * 2);
        this.ctx.fill();
    }

    // Скин "Большие милые глаза" (как у кота из Шрека)
// Скин "Большие милые глаза" (минималистичный черно-белый стиль)
drawCuteEyes() {
    const centerX = this.canvas.width / 2;
    const centerY = this.canvas.height / 2;

    // СМЕЩАЕМ ВЫШЕ - поднимаем все элементы глаз на 30 пикселей
    const eyeOffsetY = -23;

    // Добавляем случайность к частоте
    const blink = Math.sin(this.animationTime * 1.6) > 0.8 ? 0 : 1;

    if (blink === 0) {
        // ГЛАЗА ЗАКРЫТЫ - черные полоски (смещаем выше)
        this.ctx.strokeStyle = '#101115';
        this.ctx.lineWidth = 12;
        this.ctx.lineCap = 'round';

        // Левая закрытая полоска (смещаем выше)
        this.ctx.beginPath();
        this.ctx.moveTo(centerX - 90, centerY - 10);
        this.ctx.lineTo(centerX - 10, centerY - 10);
        this.ctx.stroke();

        // Правая закрытая полоска (смещаем выше)
        this.ctx.beginPath();
        this.ctx.moveTo(centerX + 10, centerY - 10);
        this.ctx.lineTo(centerX + 90, centerY - 10);
        this.ctx.stroke();

    } else {
        // ГЛАЗА ОТКРЫТЫ - огромные черно-белые КРУГЛЫЕ глаза (смещаем ВСЕ выше)

        // БЕЛКИ ГЛАЗ - огромные КРУГИ (смещаем выше)
        this.ctx.fillStyle = '#F5FCFF';
        this.ctx.strokeStyle = '#101115';
        this.ctx.lineWidth = 6;

        // Левый глаз - КРУГЛЫЙ и смещенный выше
        this.ctx.beginPath();
        this.ctx.arc(centerX - 50, centerY + eyeOffsetY, 40, 0, Math.PI * 2); // Круг радиусом 40
        this.ctx.fill();
        this.ctx.stroke();

        // Правый глаз - КРУГЛЫЙ и смещенный выше
        this.ctx.beginPath();
        this.ctx.arc(centerX + 50, centerY + eyeOffsetY, 40, 0, Math.PI * 2); // Круг радиусом 40
        this.ctx.fill();
        this.ctx.stroke();

        // ОГРОМНЫЕ ЧЕРНЫЕ ЗРАЧКИ (смещаем выше)
        this.ctx.fillStyle = '#101115';
        this.ctx.beginPath();
        this.ctx.arc(centerX - 50, centerY + eyeOffsetY, 30, 0, Math.PI * 2);
        this.ctx.arc(centerX + 50, centerY + eyeOffsetY, 30, 0, Math.PI * 2);
        this.ctx.fill();

        // ДРОЖАНИЕ ДЛЯ ОСНОВНЫХ БЛИКОВ (уменьшенная амплитуда, увеличенная скорость в 3 раза)
        const jitter = Math.sin(this.animationTime * 30) * 0.3;
        const smallJitter = Math.sin(this.animationTime * 24 + 1) * 0.2;

        // ОСНОВНЫЕ БЛИКИ - БЕЗ МЕРЦАНИЯ, только дрожание
        this.ctx.fillStyle = 'rgba(255, 255, 255, 0.87)'; // Статичный белый цвет
        this.ctx.beginPath();
        this.ctx.arc(centerX - 42 + jitter, centerY - 10 + eyeOffsetY, 12, 0, Math.PI * 2);
        this.ctx.arc(centerX + 60 + jitter, centerY - 10 + eyeOffsetY, 12, 0, Math.PI * 2);
        this.ctx.fill();

        // ВТОРИЧНЫЕ БЛИКИ - БЕЗ МЕРЦАНИЯ, только дрожание
        this.ctx.beginPath();
        this.ctx.arc(centerX - 60 + smallJitter, centerY - 15 + eyeOffsetY, 6, 0, Math.PI * 2);
        this.ctx.arc(centerX + 40 + smallJitter, centerY - 15 + eyeOffsetY, 6, 0, Math.PI * 2);
        this.ctx.fill();

        // ОДИН ПОДВИЖНЫЙ БЛИК - движется по кругу зрачка И МЕРЦАЕТ
        const movingBlinkRadius = 8;
        const movingBlinkSpeed = 1.5;

        const movingBlinkAngle = this.animationTime * movingBlinkSpeed;

        // Левый глаз - движущийся блик
        const movingBlinkX1 = centerX - 50 + Math.cos(movingBlinkAngle) * movingBlinkRadius;
        const movingBlinkY1 = centerY + eyeOffsetY + Math.sin(movingBlinkAngle) * movingBlinkRadius;

        // Правый глаз - движущийся блик (зеркально)
        const movingBlinkX2 = centerX + 50 + Math.cos(movingBlinkAngle + Math.PI) * movingBlinkRadius;
        const movingBlinkY2 = centerY + eyeOffsetY + Math.sin(movingBlinkAngle + Math.PI) * movingBlinkRadius;

        // ТОЛЬКО ЭТОТ БЛИК МЕРЦАЕТ
        const movingSparkle = Math.sin(this.animationTime * 6) * 0.3 + 0.7;
        this.ctx.fillStyle = `rgba(255, 255, 255, ${movingSparkle})`;
        this.ctx.beginPath();
        this.ctx.arc(movingBlinkX1, movingBlinkY1, 4, 0, Math.PI * 2);
        this.ctx.arc(movingBlinkX2, movingBlinkY2, 4, 0, Math.PI * 2);
        this.ctx.fill();

        // СТАТИЧНЫЕ ДОПОЛНИТЕЛЬНЫЕ БЛИКИ - БЕЗ МЕРЦАНИЯ
        this.ctx.fillStyle = 'rgba(255, 255, 255, 0.8)'; // Статичная прозрачность
        this.ctx.beginPath();
        this.ctx.arc(centerX - 25 + jitter * 0.5, centerY + 5 + eyeOffsetY, 3, 0, Math.PI * 2);
        this.ctx.arc(centerX + 75 + jitter * 0.5, centerY + 5 + eyeOffsetY, 3, 0, Math.PI * 2);
        this.ctx.fill();
    }
}
    // Скин "Афина" (богиня войны и мудрости)
    drawAthena() {
        const centerX = this.canvas.width / 2;
        const centerY = this.canvas.height / 2;
        const pulse = Math.sin(this.animationTime * 2) * 0.1 + 0.9;

        // Шлем с гребнем
        this.ctx.fillStyle = '#cd7f32'; // бронзовый
        this.ctx.strokeStyle = '#8b4513';
        this.ctx.lineWidth = 2;

        // Основа шлема
        this.ctx.beginPath();
        this.ctx.arc(centerX, centerY - 10, 25, 0, Math.PI * 2);
        this.ctx.fill();
        this.ctx.stroke();

        // Гребень шлема
        this.ctx.fillStyle = '#c0c0c0';
        this.ctx.beginPath();
        this.ctx.moveTo(centerX - 20, centerY - 35);
        this.ctx.lineTo(centerX + 20, centerY - 35);
        this.ctx.lineTo(centerX + 15, centerY - 15);
        this.ctx.lineTo(centerX - 15, centerY - 15);
        this.ctx.closePath();
        this.ctx.fill();

        // Лицо (маска)
        this.ctx.fillStyle = '#f0d9b5';
        this.ctx.beginPath();
        this.ctx.arc(centerX, centerY, 18, 0, Math.PI * 2);
        this.ctx.fill();

        // Глаза
        this.ctx.fillStyle = '#2c3e50';
        this.ctx.beginPath();
        this.ctx.arc(centerX - 8, centerY, 4, 0, Math.PI * 2);
        this.ctx.arc(centerX + 8, centerY, 4, 0, Math.PI * 2);
        this.ctx.fill();

        // Копье
        this.ctx.strokeStyle = '#8b4513';
        this.ctx.lineWidth = 3;
        this.ctx.beginPath();
        this.ctx.moveTo(centerX + 40, centerY);
        this.ctx.lineTo(centerX + 70, centerY - 20);
        this.ctx.stroke();

        // Наконечник копья
        this.ctx.fillStyle = '#c0c0c0';
        this.ctx.beginPath();
        this.ctx.moveTo(centerX + 70, centerY - 20);
        this.ctx.lineTo(centerX + 80, centerY - 25);
        this.ctx.lineTo(centerX + 75, centerY - 15);
        this.ctx.closePath();
        this.ctx.fill();

        // Сова (символ мудрости) с анимацией
        const owlY = centerY + 30 + Math.sin(this.animationTime * 3) * 2;
        this.ctx.fillStyle = '#8b7355';
        this.ctx.beginPath();
        this.ctx.arc(centerX, owlY, 8, 0, Math.PI * 2);
        this.ctx.fill();

        // Глаза совы
        this.ctx.fillStyle = '#ff6b6b';
        this.ctx.beginPath();
        this.ctx.arc(centerX - 3, owlY, 2, 0, Math.PI * 2);
        this.ctx.arc(centerX + 3, owlY, 2, 0, Math.PI * 2);
        this.ctx.fill();
    }

    // Скин "Волшебная палочка"
    drawMagicWand() {
        const centerX = this.canvas.width / 2;
        const centerY = this.canvas.height / 2;

        // Палочка
        this.ctx.strokeStyle = '#d4af37';
        this.ctx.lineWidth = 4;
        this.ctx.beginPath();
        this.ctx.moveTo(centerX - 40, centerY + 20);
        this.ctx.lineTo(centerX + 40, centerY - 20);
        this.ctx.stroke();

        // Наконечник с звездой
        this.ctx.fillStyle = '#ffd700';
        this.ctx.save();
        this.ctx.translate(centerX + 40, centerY - 20);
        this.ctx.rotate(this.animationTime);

        // Рисуем звезду
        this.ctx.beginPath();
        const spikes = 5;
        const outerRadius = 12;
        const innerRadius = 6;

        for (let i = 0; i < spikes * 2; i++) {
            const radius = i % 2 === 0 ? outerRadius : innerRadius;
            const angle = (Math.PI / spikes) * i;
            const x = Math.cos(angle) * radius;
            const y = Math.sin(angle) * radius;

            if (i === 0) {
                this.ctx.moveTo(x, y);
            } else {
                this.ctx.lineTo(x, y);
            }
        }
        this.ctx.closePath();
        this.ctx.fill();
        this.ctx.restore();

        // Волшебные искры
        for (let i = 0; i < 5; i++) {
            const angle = (this.animationTime * 2 + i * Math.PI * 0.4) % (Math.PI * 2);
            const distance = 30 + Math.sin(this.animationTime * 3 + i) * 5;
            const sparkX = centerX + Math.cos(angle) * distance;
            const sparkY = centerY + Math.sin(angle) * distance;

            this.ctx.fillStyle = `hsl(${(this.animationTime * 50 + i * 72) % 360}, 100%, 60%)`;
            this.ctx.beginPath();
            this.ctx.arc(sparkX, sparkY, 3, 0, Math.PI * 2);
            this.ctx.fill();
        }
    }

    // Скин "Принцесса"
    drawPrincess() {
        const centerX = this.canvas.width / 2;
        const centerY = this.canvas.height / 2;
        const bob = Math.sin(this.animationTime * 2) * 3;

        // Платье
        this.ctx.fillStyle = '#ff69b4';
        this.ctx.beginPath();
        this.ctx.moveTo(centerX - 30, centerY + 10);
        this.ctx.lineTo(centerX - 40, centerY + 40);
        this.ctx.lineTo(centerX + 40, centerY + 40);
        this.ctx.lineTo(centerX + 30, centerY + 10);
        this.ctx.closePath();
        this.ctx.fill();

        // Лицо
        this.ctx.fillStyle = '#f8d7b6';
        this.ctx.beginPath();
        this.ctx.arc(centerX, centerY - 10 + bob, 20, 0, Math.PI * 2);
        this.ctx.fill();

        // Глаза
        this.ctx.fillStyle = '#87ceeb';
        this.ctx.beginPath();
        this.ctx.arc(centerX - 8, centerY - 12 + bob, 4, 0, Math.PI * 2);
        this.ctx.arc(centerX + 8, centerY - 12 + bob, 4, 0, Math.PI * 2);
        this.ctx.fill();

        // Зрачки с анимацией
        const look = Math.sin(this.animationTime) * 2;
        this.ctx.fillStyle = '#000000';
        this.ctx.beginPath();
        this.ctx.arc(centerX - 8 + look, centerY - 12 + bob, 2, 0, Math.PI * 2);
        this.ctx.arc(centerX + 8 + look, centerY - 12 + bob, 2, 0, Math.PI * 2);
        this.ctx.fill();

        // Улыбка
        this.ctx.strokeStyle = '#e75480';
        this.ctx.lineWidth = 2;
        this.ctx.beginPath();
        this.ctx.arc(centerX, centerY - 5 + bob, 8, 0.1, Math.PI - 0.1);
        this.ctx.stroke();

        // Корона с анимацией блеска
        this.ctx.fillStyle = '#ffd700';
        this.ctx.beginPath();
        this.ctx.moveTo(centerX - 20, centerY - 30 + bob);
        this.ctx.lineTo(centerX - 15, centerY - 45 + bob);
        this.ctx.lineTo(centerX - 5, centerY - 35 + bob);
        this.ctx.lineTo(centerX, centerY - 50 + bob);
        this.ctx.lineTo(centerX + 5, centerY - 35 + bob);
        this.ctx.lineTo(centerX + 15, centerY - 45 + bob);
        this.ctx.lineTo(centerX + 20, centerY - 30 + bob);
        this.ctx.closePath();
        this.ctx.fill();

        // Блестки на короне
        const sparkleTime = this.animationTime * 4;
        if (Math.sin(sparkleTime) > 0.5) {
            this.ctx.fillStyle = '#ffffff';
            this.ctx.beginPath();
            this.ctx.arc(centerX, centerY - 48 + bob, 2, 0, Math.PI * 2);
            this.ctx.fill();
        }
    }

    // Скин "Фея"
    drawFairy() {
        const centerX = this.canvas.width / 2;
        const centerY = this.canvas.height / 2;
        const float = Math.sin(this.animationTime * 3) * 5;

        // Тело феи
        this.ctx.fillStyle = '#ffb6c1';
        this.ctx.beginPath();
        this.ctx.arc(centerX, centerY + float, 15, 0, Math.PI * 2);
        this.ctx.fill();

        // Крылья с анимацией
        const wingFlap = Math.sin(this.animationTime * 8) * 0.3 + 0.7;
        this.ctx.fillStyle = 'rgba(173, 216, 230, 0.6)';

        // Левое крыло
        this.ctx.save();
        this.ctx.translate(centerX - 20, centerY + float);
        this.ctx.scale(wingFlap, 1);
        this.ctx.beginPath();
        this.ctx.ellipse(0, 0, 25, 15, Math.PI/4, 0, Math.PI * 2);
        this.ctx.fill();
        this.ctx.restore();

        // Правое крыло
        this.ctx.save();
        this.ctx.translate(centerX + 20, centerY + float);
        this.ctx.scale(wingFlap, 1);
        this.ctx.beginPath();
        this.ctx.ellipse(0, 0, 25, 15, -Math.PI/4, 0, Math.PI * 2);
        this.ctx.fill();
        this.ctx.restore();

        // Волшебная пыль
        for (let i = 0; i < 8; i++) {
            const angle = this.animationTime + i * Math.PI/4;
            const distance = 40 + Math.sin(this.animationTime * 2 + i) * 10;
            const sparkX = centerX + Math.cos(angle) * distance;
            const sparkY = centerY + float + Math.sin(angle) * distance;

            this.ctx.fillStyle = `hsl(${(this.animationTime * 30 + i * 45) % 360}, 100%, 70%)`;
            this.ctx.beginPath();
            this.ctx.arc(sparkX, sparkY, 2, 0, Math.PI * 2);
            this.ctx.fill();
        }

        // Лицо
        this.ctx.fillStyle = '#f8d7b6';
        this.ctx.beginPath();
        this.ctx.arc(centerX, centerY - 8 + float, 12, 0, Math.PI * 2);
        this.ctx.fill();

        // Глаза
        this.ctx.fillStyle = '#9370db';
        this.ctx.beginPath();
        this.ctx.arc(centerX - 4, centerY - 10 + float, 2, 0, Math.PI * 2);
        this.ctx.arc(centerX + 4, centerY - 10 + float, 2, 0, Math.PI * 2);
        this.ctx.fill();

        // Волосы
        this.ctx.strokeStyle = '#ffd700';
        this.ctx.lineWidth = 3;
        for (let i = 0; i < 5; i++) {
            const curl = Math.sin(this.animationTime * 2 + i) * 0.2;
            this.ctx.beginPath();
            this.ctx.arc(centerX - 10 + i * 5, centerY - 25 + float, 8, Math.PI + curl, Math.PI * 2 - curl);
            this.ctx.stroke();
        }
    }

    // Скин "Радуга"
    drawRainbow() {
        const centerX = this.canvas.width / 2;
        const centerY = this.canvas.height / 2;
        const pulse = Math.sin(this.animationTime * 2) * 0.1 + 0.9;

        const colors = ['#ff0000', '#ff7f00', '#ffff00', '#00ff00', '#0000ff', '#4b0082', '#8b00ff'];
        const radii = [60, 55, 50, 45, 40, 35, 30];

        // Рисуем радужные дуги
        for (let i = 0; i < colors.length; i++) {
            this.ctx.strokeStyle = colors[i];
            this.ctx.lineWidth = 6 * pulse;
            this.ctx.beginPath();
            this.ctx.arc(centerX, centerY + 50, radii[i], Math.PI, Math.PI * 2);
            this.ctx.stroke();
        }

        // Облака на концах радуги с анимацией
        const cloudBob = Math.sin(this.animationTime * 3) * 2;

        // Левое облако
        this.ctx.fillStyle = '#ffffff';
        this.ctx.beginPath();
        this.ctx.arc(centerX - 55, centerY + 50 + cloudBob, 10, 0, Math.PI * 2);
        this.ctx.arc(centerX - 65, centerY + 45 + cloudBob, 8, 0, Math.PI * 2);
        this.ctx.arc(centerX - 45, centerY + 45 + cloudBob, 8, 0, Math.PI * 2);
        this.ctx.fill();

        // Правое облако
        this.ctx.beginPath();
        this.ctx.arc(centerX + 55, centerY + 50 + cloudBob, 10, 0, Math.PI * 2);
        this.ctx.arc(centerX + 65, centerY + 45 + cloudBob, 8, 0, Math.PI * 2);
        this.ctx.arc(centerX + 45, centerY + 45 + cloudBob, 8, 0, Math.PI * 2);
        this.ctx.fill();
    }
}
