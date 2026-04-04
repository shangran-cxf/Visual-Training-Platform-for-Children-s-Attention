const ParentComponents = {
    getStyles: function () {
        return `
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            body {
                font-family: 'Comic Sans MS', 'Arial', sans-serif;
                background: linear-gradient(135deg, #e8f5e8 0%, #c8e6c9 100%);
                color: #333;
                min-height: 100vh;
                display: flex;
                flex-direction: column;
            }
            .header {
                background: linear-gradient(90deg, #4caf50 0%, #81c784 99%, #81c784 100%);
                color: white;
                padding: 20px 0;
                text-align: center;
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
                position: relative;
                overflow: hidden;
            }
            .header::before {
                content: '';
                position: absolute;
                top: -50%;
                left: -50%;
                width: 200%;
                height: 200%;
                background: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><circle cx="20" cy="20" r="2" fill="rgba(255,255,255,0.3)"/><circle cx="80" cy="40" r="2" fill="rgba(255,255,255,0.3)"/><circle cx="40" cy="80" r="2" fill="rgba(255,255,255,0.3)"/><circle cx="80" cy="80" r="2" fill="rgba(255,255,255,0.3)"/></svg>');
                animation: float 20s linear infinite;
            }
            @keyframes float {
                0% { transform: translate(0, 0); }
                100% { transform: translate(100px, 100px); }
            }
            .header h1 {
                font-size: 2.2em;
                margin: 0;
                position: relative;
                z-index: 1;
                text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
                animation: pulse 2s ease-in-out infinite alternate;
            }
            @keyframes pulse {
                0% { transform: scale(1); }
                100% { transform: scale(1.03); }
            }
            .nav {
                background-color: white;
                box-shadow: 0 2px 15px rgba(0, 0, 0, 0.1);
                padding: 15px 0;
                position: sticky;
                top: 0;
                z-index: 100;
            }
            .nav ul {
                display: flex;
                justify-content: center;
                list-style: none;
                gap: 20px;
                flex-wrap: wrap;
            }
            .nav li {
                display: inline;
            }
            .nav a {
                text-decoration: none;
                color: #333;
                font-size: 16px;
                font-weight: bold;
                padding: 12px 20px;
                border-radius: 30px;
                transition: all 0.3s ease;
                position: relative;
                overflow: hidden;
                display: inline-block;
            }
            .nav a::before {
                content: '';
                position: absolute;
                top: 0;
                left: -100%;
                width: 100%;
                height: 100%;
                background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
                transition: left 0.5s;
            }
            .nav a:hover::before {
                left: 100%;
            }
            .nav a:hover {
                background-color: #4caf50;
                color: white;
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(76, 175, 80, 0.4);
            }
            .nav a.active {
                background: linear-gradient(90deg, #4caf50, #81c784);
                color: white;
                box-shadow: 0 4px 12px rgba(76, 175, 80, 0.4);
            }
            .container {
                flex: 1;
                max-width: 1800px;
                margin: 0 auto;
                padding: 30px 60px;
            }
            .footer {
                background: linear-gradient(90deg, #2e7d32 0%, #4caf50 100%);
                color: white;
                text-align: center;
                padding: 25px 0;
                margin-top: 40px;
                box-shadow: 0 -4px 15px rgba(0, 0, 0, 0.1);
            }
            .footer p {
                margin: 0;
                font-size: 16px;
                animation: pulse 2s ease-in-out infinite alternate;
            }
            @media (max-width: 768px) {
                .nav ul { gap: 10px; }
                .nav a { font-size: 14px; padding: 10px 15px; }
                .header h1 { font-size: 1.8em; }
                .container { padding: 20px; }
            }
        `;
    },

    getHeader: function () {
        return `
            <div class="header">
                <h1>儿童注意力训练平台</h1>
            </div>
        `;
    },

    getNav: function (activePage) {
        const pages = [
            { id: 'knowledge', name: '科普知识', href: 'knowledge.html' },
            { id: 'forum', name: '家长论坛', href: 'forum.html' },
            { id: 'profile', name: '个人中心', href: 'profile.html' }
        ];

        let navItems = pages.map(page => {
            const activeClass = page.id === activePage ? 'active' : '';
            return `<li><a href="${page.href}" class="${activeClass}">${page.name}</a></li>`;
        }).join('');

        return `
            <nav class="nav">
                <ul>
                    ${navItems}
                    <li><a href="#" onclick="ParentComponents.switchToChild()">切换到孩子端</a></li>
                    <li><a href="login.html" onclick="ParentComponents.logout()">退出登录</a></li>
                </ul>
            </nav>
        `;
    },

    getFooter: function () {
        return `
            <div class="footer">
                <p>© 2026 注意力训练平台</p>
            </div>
        `;
    },

    logout: function () {
        StorageUtil.removeItem('userInfo');
    },

    switchToChild: function () {
        const userInfo = StorageUtil.getItem('userInfo');
        if (userInfo && userInfo.children && userInfo.children.length > 0) {
            userInfo.mode = 'child';
            userInfo.currentChildId = userInfo.children[0].id;
            userInfo.currentChildName = userInfo.children[0].name;
            StorageUtil.setItem('userInfo', userInfo);
            window.location.href = 'child-home.html';
        }
    },

    checkAuth: function () {
        const userInfo = StorageUtil.getItem('userInfo');
        if (!userInfo) {
            window.location.href = 'login.html';
            return null;
        }
        return userInfo;
    },

    initPage: function (activePage) {
        document.head.insertAdjacentHTML('beforeend', `<style>${this.getStyles()}</style>`);

        const headerPlaceholder = document.getElementById('header-placeholder');
        const navPlaceholder = document.getElementById('nav-placeholder');
        const footerPlaceholder = document.getElementById('footer-placeholder');

        if (headerPlaceholder) headerPlaceholder.innerHTML = this.getHeader();
        if (navPlaceholder) navPlaceholder.innerHTML = this.getNav(activePage);
        if (footerPlaceholder) footerPlaceholder.innerHTML = this.getFooter();

        return this.checkAuth();
    }
};

function showPasswordModal(title, message, callback, isError = false) {
    const modal = document.createElement('div');
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-color: rgba(0, 0, 0, 0.5);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 1000;
        animation: fadeIn 0.3s ease-in-out;
    `;

    const modalContent = document.createElement('div');
    modalContent.style.cssText = `
        background: linear-gradient(135deg, #ffffff 0%, #f9f9f9 100%);
        border-radius: 20px;
        padding: 40px;
        width: 90%;
        max-width: 400px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
        position: relative;
        animation: bounceIn 0.5s ease-in-out;
        border: 4px solid #4caf50;
    `;

    const modalTitle = document.createElement('h3');
    modalTitle.textContent = title;
    modalTitle.style.cssText = `
        color: ${isError ? '#f44336' : '#2e7d32'};
        margin-bottom: 20px;
        text-align: center;
        font-size: 1.8em;
        font-family: 'Comic Sans MS', 'Arial', sans-serif;
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.1);
        animation: pulse 1.5s ease-in-out infinite alternate;
    `;

    const modalMessage = document.createElement('p');
    modalMessage.textContent = message;
    modalMessage.style.cssText = `
        color: #333;
        margin-bottom: 30px;
        text-align: center;
        font-size: 1.1em;
        font-family: 'Comic Sans MS', 'Arial', sans-serif;
    `;

    const buttonContainer = document.createElement('div');
    buttonContainer.style.cssText = `
        display: flex;
        gap: 15px;
        justify-content: center;
    `;

    const confirmButton = document.createElement('button');
    confirmButton.textContent = isError ? '确定' : '确认';
    confirmButton.style.cssText = `
        background: linear-gradient(90deg, ${isError ? '#f44336' : '#4caf50'}, ${isError ? '#ef5350' : '#81c784'});
        color: white;
        border: none;
        padding: 12px 30px;
        border-radius: 30px;
        font-size: 16px;
        font-weight: bold;
        cursor: pointer;
        transition: all 0.3s ease;
        font-family: 'Comic Sans MS', 'Arial', sans-serif;
        animation: pulse 2s ease-in-out infinite alternate;
    `;

    if (!isError) {
        const passwordInput = document.createElement('input');
        passwordInput.type = 'password';
        passwordInput.placeholder = '请输入密码';
        passwordInput.style.cssText = `
            width: 100%;
            padding: 15px;
            border: 3px solid #f0f0f0;
            border-radius: 15px;
            font-size: 16px;
            margin-bottom: 20px;
            text-align: center;
            transition: all 0.3s ease;
            font-family: 'Comic Sans MS', 'Arial', sans-serif;
        `;

        const cancelButton = document.createElement('button');
        cancelButton.textContent = '取消';
        cancelButton.style.cssText = `
            background: linear-gradient(90deg, #9e9e9e, #bdbdbd);
            color: white;
            border: none;
            padding: 12px 30px;
            border-radius: 30px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s ease;
            font-family: 'Comic Sans MS', 'Arial', sans-serif;
        `;

        cancelButton.onclick = function () {
            document.body.removeChild(modal);
        };

        confirmButton.onclick = function () {
            const password = passwordInput.value;
            document.body.removeChild(modal);
            callback(password);
        };

        passwordInput.onkeypress = function (e) {
            if (e.key === 'Enter') {
                const password = passwordInput.value;
                document.body.removeChild(modal);
                callback(password);
            }
        };

        modalContent.appendChild(passwordInput);
        buttonContainer.appendChild(cancelButton);
    } else {
        confirmButton.onclick = function () {
            document.body.removeChild(modal);
        };
    }

    modalContent.appendChild(modalTitle);
    modalContent.appendChild(modalMessage);
    modalContent.appendChild(buttonContainer);
    buttonContainer.appendChild(confirmButton);
    modal.appendChild(modalContent);
    document.body.appendChild(modal);

    if (!isError) {
        modalContent.querySelector('input').focus();
    }
}
