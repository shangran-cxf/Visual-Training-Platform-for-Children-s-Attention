// 基础UI组件

// 卡通按钮组件
class CartoonButton {
    constructor(text, onClick, options = {}) {
        this.text = text;
        this.onClick = onClick;
        this.options = {
            color: options.color || 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            size: options.size || 'medium',
            icon: options.icon || null
        };
        this.element = this.createButton();
    }

    createButton() {
        const button = document.createElement('button');
        button.textContent = this.text;

        const isGradient = this.options.color.includes('gradient');
        
        if (isGradient) {
            button.style.background = this.options.color;
        } else {
            button.style.backgroundColor = this.options.color;
        }
        button.style.color = 'white';
        button.style.border = 'none';
        button.style.borderRadius = '25px';
        button.style.fontSize = this.options.size === 'small' ? '14px' : this.options.size === 'large' ? '20px' : '16px';
        button.style.padding = this.options.size === 'small' ? '8px 16px' : this.options.size === 'large' ? '12px 24px' : '10px 20px';
        button.style.cursor = 'pointer';
        button.style.transition = 'all 0.3s ease';
        button.style.boxShadow = '0 4px 15px rgba(102, 126, 234, 0.3)';
        button.style.fontWeight = '500';

        button.addEventListener('click', this.onClick);
        button.addEventListener('touchstart', this.onClick);

        button.addEventListener('mouseover', () => {
            button.style.transform = 'translateY(-2px)';
            button.style.boxShadow = '0 6px 20px rgba(102, 126, 234, 0.4)';
        });

        button.addEventListener('mouseout', () => {
            button.style.transform = 'translateY(0)';
            button.style.boxShadow = '0 4px 15px rgba(102, 126, 234, 0.3)';
        });

        return button;
    }

    getElement() {
        return this.element;
    }
}

// 弹窗组件
class Popup {
    constructor(title, content, options = {}) {
        this.title = title;
        this.content = content;
        this.options = {
            width: options.width || '300px',
            height: options.height || 'auto',
            showClose: options.showClose !== false,
            showConfirm: options.showConfirm !== false,
            confirmText: options.confirmText || '确定',
            cancelText: options.cancelText || '取消',
            onConfirm: options.onConfirm || null,
            onCancel: options.onCancel || null
        };
        this.element = this.createPopup();
    }

    createPopup() {
        const overlay = document.createElement('div');
        overlay.style.position = 'fixed';
        overlay.style.top = '0';
        overlay.style.left = '0';
        overlay.style.width = '100%';
        overlay.style.height = '100%';
        overlay.style.backgroundColor = 'rgba(0,0,0,0.5)';
        overlay.style.display = 'flex';
        overlay.style.justifyContent = 'center';
        overlay.style.alignItems = 'center';
        overlay.style.zIndex = '1000';

        const popup = document.createElement('div');
        popup.style.backgroundColor = 'white';
        popup.style.borderRadius = '12px';
        popup.style.padding = '24px';
        popup.style.width = this.options.width;
        popup.style.height = this.options.height;
        popup.style.boxShadow = '0 10px 40px rgba(102, 126, 234, 0.3)';
        popup.style.position = 'relative';

        const title = document.createElement('h3');
        title.textContent = this.title;
        title.style.textAlign = 'center';
        title.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
        title.style.webkitBackgroundClip = 'text';
        title.style.webkitTextFillColor = 'transparent';
        title.style.backgroundClip = 'text';
        title.style.marginBottom = '15px';
        title.style.fontSize = '18px';
        title.style.fontWeight = '600';

        const content = document.createElement('div');
        content.innerHTML = this.content;
        content.style.marginBottom = '20px';
        content.style.color = '#666';
        content.style.lineHeight = '1.6';

        const buttonContainer = document.createElement('div');
        buttonContainer.style.display = 'flex';
        buttonContainer.style.justifyContent = 'space-between';
        buttonContainer.style.gap = '10px';

        if (this.options.showConfirm) {
            const confirmButton = new CartoonButton(this.options.confirmText, () => {
                if (this.options.onConfirm) {
                    this.options.onConfirm();
                }
                this.close();
            }).getElement();
            buttonContainer.appendChild(confirmButton);
        }

        const cancelButton = new CartoonButton(this.options.cancelText, () => {
            if (this.options.onCancel) {
                this.options.onCancel();
            }
            this.close();
        }, { color: '#999' }).getElement();
        buttonContainer.appendChild(cancelButton);

        if (this.options.showClose) {
            const closeButton = document.createElement('button');
            closeButton.textContent = '×';
            closeButton.style.position = 'absolute';
            closeButton.style.top = '10px';
            closeButton.style.right = '10px';
            closeButton.style.backgroundColor = 'transparent';
            closeButton.style.border = 'none';
            closeButton.style.fontSize = '24px';
            closeButton.style.cursor = 'pointer';
            closeButton.style.color = '#999';
            closeButton.style.transition = 'color 0.3s ease';
            closeButton.addEventListener('mouseover', () => {
                closeButton.style.color = '#667eea';
            });
            closeButton.addEventListener('mouseout', () => {
                closeButton.style.color = '#999';
            });
            closeButton.addEventListener('click', () => this.close());
            popup.appendChild(closeButton);
        }

        popup.appendChild(title);
        popup.appendChild(content);
        popup.appendChild(buttonContainer);
        overlay.appendChild(popup);

        return overlay;
    }

    show() {
        document.body.appendChild(this.element);
    }

    close() {
        if (this.element && this.element.parentNode) {
            this.element.parentNode.removeChild(this.element);
        }
    }
}

// 进度条组件
class ProgressBar {
    constructor(options = {}) {
        this.options = {
            width: options.width || '100%',
            height: options.height || '20px',
            backgroundColor: options.backgroundColor || '#f0f0f0',
            progressColor: options.progressColor || 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            borderRadius: options.borderRadius || '10px',
            value: options.value || 0,
            showText: options.showText !== false
        };
        this.element = this.createProgressBar();
        this.update(this.options.value);
    }

    createProgressBar() {
        const container = document.createElement('div');
        container.style.width = this.options.width;
        container.style.height = this.options.height;
        container.style.backgroundColor = this.options.backgroundColor;
        container.style.borderRadius = this.options.borderRadius;
        container.style.overflow = 'hidden';
        container.style.position = 'relative';
        container.style.boxShadow = 'inset 0 2px 4px rgba(0,0,0,0.1)';

        const progress = document.createElement('div');
        progress.style.height = '100%';
        progress.style.background = this.options.progressColor;
        progress.style.borderRadius = this.options.borderRadius;
        progress.style.transition = 'width 0.3s ease';
        progress.style.width = '0%';

        if (this.options.showText) {
            const text = document.createElement('div');
            text.style.position = 'absolute';
            text.style.top = '0';
            text.style.left = '0';
            text.style.width = '100%';
            text.style.height = '100%';
            text.style.display = 'flex';
            text.style.justifyContent = 'center';
            text.style.alignItems = 'center';
            text.style.fontSize = '12px';
            text.style.fontWeight = '600';
            text.style.color = '#333';
            text.textContent = '0%';
            container.appendChild(text);
            this.textElement = text;
        }

        container.appendChild(progress);
        this.progressElement = progress;

        return container;
    }

    update(value) {
        const percentage = Math.max(0, Math.min(100, value));
        this.progressElement.style.width = `${percentage}%`;
        if (this.textElement) {
            this.textElement.textContent = `${percentage}%`;
        }
    }

    getElement() {
        return this.element;
    }
}

// 加载动画组件
class LoadingAnimation {
    constructor(options = {}) {
        this.options = {
            size: options.size || '50px',
            color: options.color || '#667eea',
            text: options.text || '加载中...'
        };
        this.element = this.createLoading();
    }

    createLoading() {
        const container = document.createElement('div');
        container.style.display = 'flex';
        container.style.flexDirection = 'column';
        container.style.alignItems = 'center';
        container.style.justifyContent = 'center';
        container.style.padding = '20px';

        const spinner = document.createElement('div');
        spinner.style.width = this.options.size;
        spinner.style.height = this.options.size;
        spinner.style.border = `4px solid rgba(102, 126, 234, 0.2)`;
        spinner.style.borderTop = `4px solid ${this.options.color}`;
        spinner.style.borderRadius = '50%';
        spinner.style.animation = 'spin 1s linear infinite';

        const text = document.createElement('div');
        text.textContent = this.options.text;
        text.style.marginTop = '10px';
        text.style.color = '#667eea';
        text.style.fontWeight = '500';

        const style = document.createElement('style');
        style.textContent = `
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
        `;
        document.head.appendChild(style);

        container.appendChild(spinner);
        container.appendChild(text);

        return container;
    }

    show() {
        document.body.appendChild(this.element);
    }

    hide() {
        if (this.element && this.element.parentNode) {
            this.element.parentNode.removeChild(this.element);
        }
    }

    getElement() {
        return this.element;
    }
}

// 导出组件
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        CartoonButton,
        Popup,
        ProgressBar,
        LoadingAnimation
    };
}

// 全局变量，方便在HTML中使用
if (typeof window !== 'undefined') {
    window.CartoonButton = CartoonButton;
    window.Popup = Popup;
    window.ProgressBar = ProgressBar;
    window.LoadingAnimation = LoadingAnimation;
}
