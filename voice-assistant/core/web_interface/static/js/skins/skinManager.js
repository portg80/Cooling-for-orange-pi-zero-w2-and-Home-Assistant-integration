class SkinManager {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        if (!this.canvas) {
            console.error(`Canvas with id '${canvasId}' not found!`);
            return;
        }

        this.ctx = this.canvas.getContext('2d');
        this.skinDrawers = new SkinDrawers(this.ctx, this.canvas);
        this.currentSkins = new Map();
        this.animations = new Map();
        this.isBlinking = false;
        this.currentSkin = 'default';

        this._setupCanvas();
        this._loadDefaultSkins();
        this._setupSkinPanel();
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

    _setupSkinPanel() {
        const skinMenuBtn = document.getElementById('skinMenuBtn');
        const skinPanel = document.getElementById('skinPanel');

        if (skinMenuBtn && skinPanel) {
            skinMenuBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                skinPanel.classList.toggle('active');
            });

            document.addEventListener('click', (e) => {
                if (!skinPanel.contains(e.target) && e.target !== skinMenuBtn) {
                    skinPanel.classList.remove('active');
                }
            });

            const skinItems = document.querySelectorAll('.skin-item');
            skinItems.forEach(item => {
                item.addEventListener('click', () => {
                    const skinName = item.getAttribute('data-skin');
                    this.applySkin(skinName);

                    skinItems.forEach(i => i.classList.remove('active'));
                    item.classList.add('active');

                    skinPanel.classList.remove('active');
                });
            });
        }
    }

_loadDefaultSkins() {
    this.availableSkins = {
        'default': {
            name: 'По умолчанию',
            elements: [],
            icon: 'bi-circle'
        },
        'eyes': {
            name: 'Глаза',
            elements: [
                { type: 'dom', html: this._createEyesHTML() }
            ],
            icon: 'bi-eye'
        },
        'glasses': {
            name: 'Очки',
            elements: [
                { type: 'canvas', draw: 'glasses' }
            ],
            icon: 'bi-eyeglasses'
        },
        'robot': {
            name: 'Робот',
            elements: [
                { type: 'canvas', draw: 'robotEyes' }
            ],
            icon: 'bi-cpu'
        },
        'heart': {
            name: 'Сердце',
            elements: [
                { type: 'canvas', draw: 'heart' }
            ],
            icon: 'bi-heart'
        },
        'star': {
            name: 'Звезда',
            elements: [
                { type: 'canvas', draw: 'star' }
            ],
            icon: 'bi-star'
        },
        'cat': {
            name: 'Кошка',
            elements: [
                { type: 'canvas', draw: 'cat' }
            ],
            icon: 'bi-heart-fill'
        },
        'alien': {
            name: 'Пришелец',
            elements: [
                { type: 'canvas', draw: 'alien' }
            ],
            icon: 'bi-rocket'
        },
        // НОВЫЕ СКИНЫ:
        'friedEgg': {
            name: 'Яичница',
            elements: [
                { type: 'canvas', draw: 'friedEgg' }
            ],
            icon: 'bi-egg-fried'
        },
        'cuteEyes': {
            name: 'Милые глазки',
            elements: [
                { type: 'canvas', draw: 'cuteEyes' }
            ],
            icon: 'bi-eye-fill'
        },
        'athena': {
            name: 'Афина',
            elements: [
                { type: 'canvas', draw: 'athena' }
            ],
            icon: 'bi-shield-fill'
        },
        'magicWand': {
            name: 'Волшебная палочка',
            elements: [
                { type: 'canvas', draw: 'magicWand' }
            ],
            icon: 'bi-magic'
        },
        'princess': {
            name: 'Принцесса',
            elements: [
                { type: 'canvas', draw: 'princess' }
            ],
            icon: 'bi-emoji-sunglasses'
        },
        'fairy': {
            name: 'Фея',
            elements: [
                { type: 'canvas', draw: 'fairy' }
            ],
            icon: 'bi-flower1'
        },
        'rainbow': {
            name: 'Радуга',
            elements: [
                { type: 'canvas', draw: 'rainbow' }
            ],
            icon: 'bi-droplet-half'
        }
    };
}


    _createEyesHTML() {
        return `
            <div class="eyes skin-element">
                <div class="eye">
                    <div class="pupil"></div>
                    <div class="eyelid"></div>
                </div>
                <div class="eye">
                    <div class="pupil"></div>
                    <div class="eyelid"></div>
                </div>
            </div>
        `;
    }

    _createGlassesHTML() {
        return `
            <div class="glasses skin-element">
                <div class="glass-frame"></div>
                <div class="glass-bridge"></div>
            </div>
        `;
    }

    applySkin(skinName) {
        this.clearSkins();
        this.currentSkin = skinName;

        const skin = this.availableSkins[skinName];
        if (!skin) return;

        skin.elements.forEach(element => {
            if (element.type === 'dom') {
                this._addDOMElement(element.html);
            } else if (element.type === 'canvas') {
                // Сохраняем название метода для отрисовки
                this.animations.set(skinName, element.draw);
            }
        });

        localStorage.setItem('selectedSkin', skinName);
        console.log(`Скин "${skinName}" применен`);
    }

    _addDOMElement(html) {
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = html;
        const element = tempDiv.firstElementChild;

        const skinOverlay = document.getElementById('skin-overlay');
        skinOverlay.appendChild(element);

        if (element.classList.contains('eyes')) {
            this._startBlinking();
        }
    }

    _startBlinking() {
        if (this.isBlinking) return;

        this.isBlinking = true;
        const blink = () => {
            const eyelids = document.querySelectorAll('.eyelid');
            eyelids.forEach(eyelid => {
                eyelid.style.top = '0';
            });

            setTimeout(() => {
                eyelids.forEach(eyelid => {
                    eyelid.style.top = '-100%';
                });
            }, 200);

            const nextBlink = 2000 + Math.random() * 4000;
            setTimeout(blink, nextBlink);
        };

        blink();
    }

    clearSkins() {
        const skinOverlay = document.getElementById('skin-overlay');
        skinOverlay.innerHTML = '';

        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        this.animations.clear();
        this.isBlinking = false;
    }

    draw() {
        // Обновляем время для анимаций
        this.skinDrawers.updateTime();

        // Очищаем canvas
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

        // Выполняем все активные анимации через skinDrawers
        this.animations.forEach(drawMethodName => {
            if (this.skinDrawers[`draw${drawMethodName.charAt(0).toUpperCase() + drawMethodName.slice(1)}`]) {
                this.skinDrawers[`draw${drawMethodName.charAt(0).toUpperCase() + drawMethodName.slice(1)}`]();
            }
        });
    }

    startAnimation() {
        const animate = () => {
            this.draw();
            requestAnimationFrame(animate);
        };
        animate();
    }

    loadSavedSkin() {
        const savedSkin = localStorage.getItem('selectedSkin');
        if (savedSkin && this.availableSkins[savedSkin]) {
            this.applySkin(savedSkin);

            // Активируем соответствующий элемент в панели
            const skinItem = document.querySelector(`[data-skin="${savedSkin}"]`);
            if (skinItem) {
                document.querySelectorAll('.skin-item').forEach(item => {
                    item.classList.remove('active');
                });
                skinItem.classList.add('active');
            }
        }
    }
}
