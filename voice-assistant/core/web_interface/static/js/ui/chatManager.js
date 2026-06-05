class ChatManager {
    constructor(containerId, apiClient) {
        this.container = document.getElementById(containerId);
        this.apiClient = apiClient;
        this._bindGlobalEvents();
    }

    // Добавляем метод для проверки последнего сообщения
    isLastMessageRepeatCommand(commandText) {
        const messages = this.container.querySelectorAll('.message-bubble');
        if (messages.length === 0) return false;

        const lastMessage = messages[messages.length - 1];
        const lastMessageText = lastMessage.querySelector('.message-text').textContent;
        const expectedRepeatText = `Повтор команды: ${commandText}`;

        return lastMessageText === expectedRepeatText;
    }

    _bindGlobalEvents() {
        // Обработчик клика вне сообщений для сворачивания
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.message-bubble')) {
                this.collapseAllMessages();
            }
        });

        // Обработчики для кнопок действий
        this.container.addEventListener('click', (e) => {
            if (e.target.closest('.copy-btn')) {
                e.stopPropagation();
                this.copyMessage(e.target.closest('.copy-btn'));
            } else if (e.target.closest('.delete-btn')) {
                e.stopPropagation();
                this.deleteMessage(e.target.closest('.delete-btn'));
            } else if (e.target.closest('.repeat-btn')) {
                e.stopPropagation();
                this.repeatMessage(e.target.closest('.repeat-btn'));
            }
        });
    }

    addMessage(text, type = 'info') {
        const messageDiv = document.createElement('div');

        let className = 'message-bubble ';
        switch(type) {
            case 'recognized_speech':
                className += 'user-message';
                break;
            case 'error':
                className += 'error-message';
                break;
            case 'repeat': // ДОБАВЛЯЕМ НОВЫЙ ТИП ДЛЯ ПОВТОРОВ
                className += 'repeat-message';
                break;
            default:
                className += 'assistant-message';
        }

        messageDiv.className = className;
        messageDiv.setAttribute('data-message-text', text);
        messageDiv.setAttribute('data-message-type', type);

        const timestamp = new Date().toLocaleTimeString();

        // Формируем HTML в зависимости от типа сообщения
        let actionsHTML = '';
        if (type === 'recognized_speech') {
            actionsHTML = `
                <button class="action-btn repeat-btn">
                    <i class="bi bi-arrow-repeat"></i> Повторить
                </button>
                <button class="action-btn copy-btn">
                    <i class="bi bi-copy"></i> Копировать
                </button>
                <button class="action-btn delete-btn">
                    <i class="bi bi-trash"></i> Удалить
                </button>
            `;
        } else {
            actionsHTML = `
                <button class="action-btn copy-btn">
                    <i class="bi bi-copy"></i> Копировать
                </button>
                <button class="action-btn delete-btn">
                    <i class="bi bi-trash"></i> Удалить
                </button>
            `;
        }

        messageDiv.innerHTML = `
            <div class="message-content">
                <div class="message-text">${text}</div>
                <div class="message-extra">
                    <div class="d-flex justify-content-between align-items-center">
                        <small class="message-timestamp">${timestamp} - ${type}</small>
                        <div class="message-actions">
                            ${actionsHTML}
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Добавляем обработчик клика для разворачивания
        messageDiv.addEventListener('click', (e) => {
            // Проверяем, что клик не по кнопкам действий
            if (!e.target.closest('.action-btn')) {
                this.toggleMessage(messageDiv);
            }
        });

        this.container.appendChild(messageDiv);
        this.container.scrollTop = this.container.scrollHeight;
    }

    toggleMessage(messageElement) {
        const isExpanded = messageElement.classList.contains('expanded');

        // Сворачиваем все сообщения
        this.collapseAllMessages();

        // Если сообщение не было развернуто, разворачиваем его
        if (!isExpanded) {
            messageElement.classList.add('expanded');
        }
    }

    collapseAllMessages() {
        const expandedMessages = this.container.querySelectorAll('.message-bubble.expanded');
        expandedMessages.forEach(msg => {
            msg.classList.remove('expanded');
        });
    }

    copyMessage(copyButton) {
        const messageElement = copyButton.closest('.message-bubble');
        const messageText = messageElement.querySelector('.message-text').textContent;

        navigator.clipboard.writeText(messageText).then(() => {
            // Временная обратная связь
            const originalText = copyButton.innerHTML;
            copyButton.innerHTML = '<i class="bi bi-check"></i> Скопировано';
            copyButton.style.background = 'rgba(52, 168, 83, 0.5)';

            setTimeout(() => {
                copyButton.innerHTML = originalText;
                copyButton.style.background = '';
            }, 2000);
        }).catch(err => {
            console.error('Ошибка копирования: ', err);
            copyButton.innerHTML = '<i class="bi bi-x"></i> Ошибка';
            copyButton.style.background = 'rgba(234, 67, 53, 0.5)';

            setTimeout(() => {
                copyButton.innerHTML = '<i class="bi bi-copy"></i> Копировать';
                copyButton.style.background = '';
            }, 2000);
        });
    }

    deleteMessage(deleteButton) {
        const messageElement = deleteButton.closest('.message-bubble');

        // Анимация удаления
        messageElement.style.opacity = '0';
        messageElement.style.transform = 'translateX(-100%)';
        messageElement.style.transition = 'all 0.3s ease';

        setTimeout(() => {
            messageElement.remove();
        }, 300);
    }

    repeatMessage(repeatButton) {
        const messageElement = repeatButton.closest('.message-bubble');
        const messageText = messageElement.getAttribute('data-message-text');

        if (messageText) {
            // ПРОВЕРЯЕМ: если последнее сообщение уже является повтором этой команды - не добавляем новое
            if (!this.isLastMessageRepeatCommand(messageText)) {
                this.addMessage(`Повтор команды: ${messageText}`, 'repeat');
            }

            // Визуальная обратная связь
            const originalText = repeatButton.innerHTML;
            repeatButton.innerHTML = '<i class="bi bi-arrow-repeat"></i> Отправка...';
            repeatButton.disabled = true;

            // Отправляем команду на сервер (ВСЕГДА отправляем, даже если сообщение о повторе не добавили)
            this.apiClient.sendTextCommand(messageText)
                .then(response => {
                    repeatButton.innerHTML = '<i class="bi bi-check"></i> Отправлено';
                    repeatButton.style.background = 'rgba(52, 168, 83, 0.5)';

                    setTimeout(() => {
                        repeatButton.innerHTML = originalText;
                        repeatButton.style.background = '';
                        repeatButton.disabled = false;
                    }, 2000);
                })
                .catch(error => {
                    console.error('Ошибка повторной отправки: ', error);
                    repeatButton.innerHTML = '<i class="bi bi-x"></i> Ошибка';
                    repeatButton.style.background = 'rgba(234, 67, 53, 0.5)';

                    setTimeout(() => {
                        repeatButton.innerHTML = originalText;
                        repeatButton.style.background = '';
                        repeatButton.disabled = false;
                    }, 2000);
                });
        }
    }

    clear() {
        this.container.innerHTML = '';
    }
}
