/**
 * 家长端通用组件库
 * 提供统一的样式、导航、弹窗等功能
 */

const ParentComponents = {
    /**
     * 获取通用CSS样式
     */
    getStyles: function () {
        return `
            /* ===== CSS变量 ===== */
            :root {
                --primary: #4F46E5;
                --primary-light: #818CF8;
                --secondary: #F97316;
                --secondary-light: #FDBA74;
                --bg-color: #EEF2FF;
                --card-bg: #FFFFFF;
                --text-dark: #1E1B4B;
                --text-light: #6366F1;
                --accent-green: #CEEFDD;
                --accent-pink: #EC4899;
                --accent-yellow: #F2E1C4;
                --accent-cyan: #06B6D4;
                --shadow-soft: 0 8px 32px rgba(79, 70, 229, 0.15);
                --shadow-card: 0 4px 20px rgba(0, 0, 0, 0.08), inset 0 2px 0 rgba(255, 255, 255, 0.8);
                --shadow-pressed: inset 0 3px 8px rgba(0, 0, 0, 0.12);
            }

            /* ===== 基础样式 ===== */
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
                font-family: 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            }

            html, body {
                overflow-x: hidden;
            }

            body {
                background: #f2f0faff;
                color: var(--text-dark);
                min-height: 100vh;
                display: flex;
                gap: 24px;
                padding: 24px;
            }

            /* ===== 侧边栏样式 ===== */
            .sidebar {
                width: 130px;
                background: #886ab4;
                box-shadow: 0 8px 32px rgba(46, 19, 68, 0.15), 0 4px 16px rgba(15, 14, 14, 0.1);
                padding: 24px 0;
                display: flex;
                flex-direction: column;
                align-items: center;
                gap: 20px;
                border-radius: 32px;
                position: relative;
            }

            /* 用户头像 */
            .user-avatar-sidebar {
                width: 85px;
                height: 85px;
                margin-top: 25px;
                margin-bottom: -50px;
                border-radius: 50%;
                background: linear-gradient(145deg, #F8FAFC 0%, #F1F5F9 100%);
                display: flex;
                align-items: center;
                justify-content: center;
                overflow: hidden;
                border: 3px solid #343559;
                cursor: pointer;
                transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
            }

            .user-avatar-sidebar:hover {
                transform: scale(1.1);
            }

            .user-avatar-sidebar img {
                width: 100%;
                height: 100%;
                object-fit: cover;
            }

            /* 分割线 */
            .divider {
                width: 60px;
                height: 2px;
                background: rgba(255, 255, 255, 0.3);
                border-radius: 1px;
                margin: 15px 0;
            }

            .top-divider {
                margin-top: 60px;
                margin-bottom: -10px;
            }

            /* 导航项 */
            .nav-item {
                width: 75px;
                height: 75px;
                margin-left: 12px;
                margin-right: 12px;
                margin-top: 15px;
                border-radius: 20px;
                background: #FFFFFF;
                color: #000000;
                font-size: 16px;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                cursor: pointer;
                transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
                border: 3px solid transparent;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06), inset 0 2px 0 rgba(255, 255, 255, 0.8);
                position: relative;
                overflow: hidden;
                text-decoration: none;
            }

            .first-nav-item {
                margin-top: 30px;
            }

            .nav-item:hover {
                transform: translateY(-4px) scale(1.02);
            }

            .nav-item.active {
                background: #543b7c;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
            }

            .nav-item.active .nav-icon,
            .nav-item.active .nav-label {
                color: white;
            }

            .nav-icon {
                width: 28px;
                height: 28px;
                transition: transform 0.3s ease;
            }

            .nav-item:hover .nav-icon {
                transform: scale(1.1);
            }

            .nav-label {
                font-size: 11px;
                font-weight: 600;
                color: var(--text-dark);
                margin-top: 4px;
                transition: color 0.3s ease;
            }

            /* 登出按钮 */
            .logout-btn {
                position: absolute;
                bottom: 24px;
                width: 55px;
                height: 55px;
                border-radius: 16px;
                background: rgba(255, 255, 255, 0.9);
                display: flex;
                align-items: center;
                justify-content: center;
                cursor: pointer;
                transition: all 0.3s ease;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
                border: 2px solid transparent;
                margin-bottom: 30px;
            }

            .logout-btn:hover {
                transform: scale(1.05);
                background: #fff;
                border-color: #ff6b6b;
            }

            .logout-btn svg {
                width: 25px;
                height: 25px;
                color: #343559;
            }

            .logout-btn:hover svg {
                color: #ff6b6b;
            }

            /* ===== 主内容区域 ===== */
            .main-content {
                flex: 1;
                padding: 24px;
                overflow-y: auto;
                max-width: calc(100% - 154px);
            }

            /* ===== 卡片基础样式 ===== */
            .card {
                background: #f9f6f1;
                border-radius: 20px;
                padding: 24px;
                box-shadow: 8px 8px 16px rgba(236, 239, 244, 0.6), -8px -8px 16px rgba(239, 236, 255, 0.8);
            }

            .card-header {
                font-size: 20px;
                font-weight: 600;
                margin-bottom: 20px;
                color: #343559;
            }

            /* ===== 按钮样式 ===== */
            .btn-primary {
                padding: 15px 10px;
                background: linear-gradient(135deg, #773ada 0%, #451594 100%);
                color: white;
                border: none;
                border-radius: 8px;
                cursor: pointer;
                font-size: 14px;
                font-weight: 500;
                transition: all 0.3s ease;
            }

            .btn-primary:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
            }

            .btn-secondary {
                padding: 10px 20px;
                background: #f0f0f0;
                color: #666;
                border: none;
                border-radius: 8px;
                cursor: pointer;
                font-size: 14px;
                font-weight: 500;
                transition: all 0.3s ease;
            }

            .btn-secondary:hover {
                background: #e0e0e0;
            }

            /* ===== 弹窗样式 ===== */
            .modal-overlay {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0, 0, 0, 0.5);
                display: none;
                align-items: center;
                justify-content: center;
                z-index: 1000;
            }

            .modal-overlay.show {
                display: flex;
            }

            .modal-content {
                background: white;
                border-radius: 20px;
                padding: 30px;
                max-width: 500px;
                width: 90%;
                max-height: 90vh;
                overflow-y: auto;
                position: relative;
                animation: modalSlideIn 0.3s ease;
            }

            @keyframes modalSlideIn {
                from {
                    opacity: 0;
                    transform: translateY(-20px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }

            .modal-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 25px;
                padding-bottom: 15px;
                border-bottom: 2px solid #f0f0f0;
            }

            .modal-header h3 {
                margin: 0;
                color: #271151;
                font-size: 25px;
                font-weight: 600;
            }

            .modal-close {
                background: none;
                border: none;
                font-size: 40px;
                cursor: pointer;
                color: #cca4e1;
                padding: 0;
                width: 50px;
                height: 50px;
                display: flex;
                align-items: center;
                justify-content: center;
                border-radius: 50%;
                transition: all 0.3s ease;
            }

            .modal-close:hover {
                background: #e8e7ff;
                color: #8849a7;
            }

            /* ===== 表单样式 ===== */
            .form-group {
                margin-bottom: 15px;
            }

            .form-group label {
                display: block;
                font-size: 15px;
                font-weight: 500;
                color: #271151;
                margin-bottom: 5px;
            }

            .form-group input {
                width: 100%;
                padding: 10px 14px;
                border: 2px solid #e8e8e8;
                border-radius: 8px;
                font-size: 14px;
                transition: all 0.3s ease;
            }

            .form-group input:focus {
                outline: none;
                border-color: #667eea;
            }

            .form-group input:disabled {
                background-color: #f5f5f5;
                cursor: not-allowed;
                opacity: 0.6;
            }

            .form-group input.valid {
                border-color: #27ae60;
            }

            .form-group input.invalid {
                border-color: #e74c3c;
            }

            .password-error {
                color: #e74c3c;
                font-size: 15px;
                margin-top: 15px;
                margin-bottom: -17px;
                min-height: 16px;
            }

            /* ===== 响应式设计 ===== */
            @media (max-width: 1200px) {
                .main-content {
                    grid-template-columns: 1fr;
                }
            }

            @media (max-width: 768px) {
                body {
                    flex-direction: column;
                    padding: 12px;
                }

                .sidebar {
                    width: 100%;
                    flex-direction: row;
                    padding: 12px;
                    gap: 10px;
                }

                .main-content {
                    max-width: 100%;
                }
            }
        `;
    },

    /**
     * 获取侧边栏HTML
     * @param {string} activePage - 当前活动页面ID
     */
    getSidebar: function (activePage = '') {
        const navItems = [
            { id: 'profile', label: '儿童档案', href: 'child-document.html', icon: this.getIcons().document },
            { id: 'knowledge', label: '科普知识', href: 'knowledge.html', icon: this.getIcons().book },
            { id: 'forum', label: '论坛', href: 'forum.html', icon: this.getIcons().message },
            { id: 'child', label: '儿童端', href: '#', icon: this.getIcons().game, action: 'ParentComponents.switchToChildMode(); return false;' }
        ];

        let navItemsHtml = navItems.map((item, index) => {
            const activeClass = item.id === activePage ? 'active' : '';
            const firstClass = index === 0 ? 'first-nav-item' : '';
            const clickAction = item.action ? `onclick="${item.action}; return false;"` : '';

            return `
                <a href="${item.href}" class="nav-item ${activeClass} ${firstClass}" ${clickAction}>
                    <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        ${item.icon}
                    </svg>
                    <span class="nav-label">${item.label}</span>
                </a>
            `;
        }).join('');

        // 获取用户头像
        let avatarHtml = `
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#343559" stroke-width="2">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                <circle cx="12" cy="7" r="4"></circle>
            </svg>
        `;

        // 尝试从本地存储获取用户信息
        const userInfo = StorageUtil.getItem('userInfo');
        if (userInfo && userInfo.avatar) {
            avatarHtml = `<img src="${userInfo.avatar}" alt="用户头像" style="width: 100%; height: 100%; object-fit: cover;">`;
        }

        return `
            <div class="sidebar">
                <div class="user-avatar-sidebar" onclick="ParentComponents.showProfileModal()" data-avatar-updatable="true">
                    ${avatarHtml}
                </div>
                <div class="divider top-divider"></div>
                ${navItemsHtml}
                <div class="divider"></div>
                <div class="logout-btn" onclick="ParentComponents.logout()">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
                        <polyline points="16 17 21 12 16 7"></polyline>
                        <line x1="21" y1="12" x2="9" y2="12"></line>
                    </svg>
                </div>
            </div>
            <script>
                // 页面加载后检查并更新头像
                setTimeout(() => {
                    const sidebarAvatar = document.querySelector('.user-avatar-sidebar[data-avatar-updatable="true"]');
                    if (sidebarAvatar) {
                        const userInfo = StorageUtil.getItem('userInfo');
                        if (userInfo && userInfo.avatar) {
                            sidebarAvatar.innerHTML = '<img src="' + userInfo.avatar + '" alt="用户头像" style="width: 100%; height: 100%; object-fit: cover;">';
                        }
                    }
                }, 500);
            </script>
        `;
    },

    /**
     * 获取个人中心弹窗HTML
     */
    getProfileModal: function () {
        return `
            <div class="modal-overlay" id="profile-modal">
                <div class="modal-content profile-modal-content">
                    <div class="modal-header">
                        <h3>个人中心</h3>
                        <button class="modal-close" onclick="ParentComponents.closeProfileModal()">&times;</button>
                    </div>
                    <div class="profile-header">
                        <div class="avatar-section">
                            <div class="avatar-large" id="modal-avatar" onclick="document.getElementById('modal-avatar-input').click()">
                                <span id="modal-avatar-initial">U</span>
                            </div>
                            <div class="avatar-upload-hint">点击上传头像</div>
                            <input type="file" id="modal-avatar-input" accept="image/*" onchange="ParentComponents.uploadAvatar(event)">
                        </div>
                        <div class="profile-info">
                            <div class="profile-username" id="profile-username">加载中...</div>
                            <div class="profile-meta">
                                <div class="profile-meta-item">UID: <span id="profile-uid">-</span></div>
                                <div class="profile-meta-item">注册时间: <span id="profile-created">-</span></div>
                                <div class="profile-meta-item">邮箱: <span id="profile-email-display">-</span></div>
                            </div>
                        </div>
                    </div>
                    <div class="profile-actions-outside">
                        <button class="edit-btn" onclick="ParentComponents.toggleEditMode()">编辑</button>
                    </div>
                    <div class="edit-profile-section" id="edit-profile-section" style="display: none;">
                        <h4>编辑个人信息</h4>
                        <form class="edit-form" onsubmit="return false;" autocomplete="on">
                            <div class="form-group">
                                <label for="edit-username">用户名</label>
                                <input type="text" id="edit-username" placeholder="请输入用户名" autocomplete="username">
                            </div>
                            <div class="form-group">
                                <label for="edit-email">邮箱</label>
                                <input type="email" id="edit-email" placeholder="请输入邮箱" autocomplete="email">
                            </div>
                            <div class="form-group">
                                <label for="edit-old-password">旧密码</label>
                                <input type="password" id="edit-old-password" placeholder="请输入旧密码" oninput="ParentComponents.verifyOldPassword()" autocomplete="current-password">
                                <div class="password-error" id="old-password-error"></div>
                            </div>
                            <div class="form-group">
                                <label for="edit-password">新密码</label>
                                <input type="password" id="edit-password" placeholder="请输入新密码" disabled autocomplete="new-password">
                            </div>
                            <div class="form-group">
                                <label for="edit-confirm-password">确认新密码</label>
                                <input type="password" id="edit-confirm-password" placeholder="请再次输入新密码" disabled autocomplete="new-password">
                                <div class="password-error" id="confirm-password-error"></div>
                            </div>
                            <div class="form-actions">
                                <button type="button" class="btn-secondary" onclick="ParentComponents.cancelEdit()">取消</button>
                                <button type="button" class="btn-primary" onclick="ParentComponents.saveProfile()">保存</button>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        `;
    },

    /**
     * 获取图标SVG路径
     */
    getIcons: function () {
        return {
            document: '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline>',
            book: '<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path>',
            message: '<path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"></path>',
            game: '<rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect><line x1="8" y1="21" x2="16" y2="21"></line><line x1="12" y1="17" x2="12" y2="21"></line>'
        };
    },

    /**
     * 初始化页面
     * @param {string} activePage - 当前活动页面ID
     */
    initPage: function (activePage = '') {
        // 插入样式
        const styleElement = document.createElement('style');
        styleElement.textContent = this.getStyles();
        document.head.appendChild(styleElement);

        // 插入侧边栏
        const sidebarHtml = this.getSidebar(activePage);
        document.body.insertAdjacentHTML('afterbegin', sidebarHtml);

        // 插入个人中心弹窗
        const modalHtml = this.getProfileModal();
        document.body.insertAdjacentHTML('beforeend', modalHtml);

        // 加载用户信息
        this.loadProfileInfo();
    },

    /**
     * 显示个人中心弹窗
     */
    showProfileModal: function () {
        const modal = document.getElementById('profile-modal');
        if (modal) {
            modal.classList.add('show');
            this.loadProfileInfo();
        }
    },

    /**
     * 关闭个人中心弹窗
     */
    closeProfileModal: function () {
        const modal = document.getElementById('profile-modal');
        if (modal) {
            modal.classList.remove('show');
            this.cancelEdit();
        }
    },

    /**
     * 加载用户信息
     */
    loadProfileInfo: async function () {
        const userInfo = StorageUtil.getItem('userInfo');
        if (!userInfo) return;

        const uidElement = document.getElementById('profile-uid');
        const usernameElement = document.getElementById('profile-username');
        const emailElement = document.getElementById('profile-email-display');
        const createdElement = document.getElementById('profile-created');
        const avatarElement = document.getElementById('modal-avatar');
        const avatarInitialElement = document.getElementById('modal-avatar-initial');
        const sidebarAvatar = document.querySelector('.user-avatar-sidebar');

        if (uidElement) uidElement.textContent = userInfo.uid || '-';
        if (usernameElement) usernameElement.textContent = userInfo.username || '加载中...';

        try {
            const response = await fetch(`/api/user/query?type=id&value=${userInfo.parent_id}`);
            const result = await response.json();
            const data = result.data || result;

            if (usernameElement) usernameElement.textContent = data.username || userInfo.username || '-';
            if (emailElement) emailElement.textContent = data.email || '-';
            if (createdElement && data.created_at) createdElement.textContent = data.created_at.split(' ')[0];

            // 填充编辑表单
            const editUsername = document.getElementById('edit-username');
            const editEmail = document.getElementById('edit-email');
            if (editUsername) editUsername.value = data.username || userInfo.username || '';
            if (editEmail) editEmail.value = data.email || '';

            // 设置头像
            if (data.avatar) {
                // 更新本地存储中的头像URL
                userInfo.avatar = data.avatar;
                StorageUtil.setItem('userInfo', userInfo);

                // 更新弹窗头像
                if (avatarElement) {
                    avatarElement.innerHTML = `<img src="${data.avatar}" alt="头像">`;
                }

                // 更新侧边栏头像
                if (sidebarAvatar) {
                    sidebarAvatar.innerHTML = `<img src="${data.avatar}" alt="用户头像" style="width: 100%; height: 100%; object-fit: cover;">`;
                }
            } else if (avatarInitialElement) {
                const initial = (data.username || userInfo.username || 'U').charAt(0).toUpperCase();
                avatarInitialElement.textContent = initial;
            }
        } catch (err) {
            console.error('获取用户信息失败:', err);
        }
    },

    /**
     * 切换编辑模式
     */
    toggleEditMode: function () {
        const editSection = document.getElementById('edit-profile-section');
        const editButton = document.querySelector('.profile-actions-outside');
        const modalContent = document.querySelector('.profile-modal-content');

        if (editSection && editButton) {
            if (editSection.style.display === 'none') {
                editButton.style.display = 'none';
                editSection.style.display = 'block';
                if (modalContent) modalContent.style.minHeight = '750px';
            } else {
                editButton.style.display = 'block';
                editSection.style.display = 'none';
                if (modalContent) modalContent.style.minHeight = '200px';
            }
        }
    },

    /**
     * 取消编辑
     */
    cancelEdit: function () {
        const editSection = document.getElementById('edit-profile-section');
        const editButton = document.querySelector('.profile-actions-outside');
        const modalContent = document.querySelector('.profile-modal-content');

        if (editSection) editSection.style.display = 'none';
        if (editButton) editButton.style.display = 'block';
        if (modalContent) modalContent.style.minHeight = '200px';

        // 重置表单
        const userInfo = StorageUtil.getItem('userInfo');
        const editUsername = document.getElementById('edit-username');
        const editEmail = document.getElementById('edit-email');
        const oldPassword = document.getElementById('edit-old-password');
        const newPassword = document.getElementById('edit-password');
        const confirmPassword = document.getElementById('edit-confirm-password');
        const oldPasswordError = document.getElementById('old-password-error');

        if (editUsername && userInfo) editUsername.value = userInfo.username || '';
        if (editEmail) editEmail.value = '';
        if (oldPassword) oldPassword.value = '';
        if (newPassword) {
            newPassword.value = '';
            newPassword.disabled = true;
        }
        if (confirmPassword) {
            confirmPassword.value = '';
            confirmPassword.disabled = true;
        }
        if (oldPasswordError) oldPasswordError.textContent = '';

        this.oldPasswordVerified = false;
    },

    /**
     * 验证旧密码
     */
    verifyOldPassword: async function () {
        const oldPasswordInput = document.getElementById('edit-old-password');
        const newPasswordInput = document.getElementById('edit-password');
        const confirmPasswordInput = document.getElementById('edit-confirm-password');
        const errorElement = document.getElementById('old-password-error');

        if (!oldPasswordInput) return;

        const oldPassword = oldPasswordInput.value.trim();

        if (!oldPassword) {
            if (errorElement) errorElement.textContent = '';
            if (newPasswordInput) newPasswordInput.disabled = true;
            if (confirmPasswordInput) confirmPasswordInput.disabled = true;
            this.oldPasswordVerified = false;
            return;
        }

        const userInfo = StorageUtil.getItem('userInfo');
        if (!userInfo) return;

        try {
            const response = await fetch('/api/user/verify-password', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    parent_id: userInfo.parent_id,
                    old_password: oldPassword
                })
            });

            const result = await response.json();
            const data = result.data || result;

            if (response.ok && data.valid) {
                if (errorElement) errorElement.textContent = '';
                if (newPasswordInput) newPasswordInput.disabled = false;
                if (confirmPasswordInput) confirmPasswordInput.disabled = false;
                this.oldPasswordVerified = true;
            } else {
                if (errorElement) errorElement.textContent = '旧密码错误，请重新输入！';
                if (newPasswordInput) newPasswordInput.disabled = true;
                if (confirmPasswordInput) confirmPasswordInput.disabled = true;
                this.oldPasswordVerified = false;
            }
        } catch (err) {
            console.error('验证旧密码失败:', err);
            if (errorElement) errorElement.textContent = '验证失败，请稍后再试';
        }
    },

    /**
     * 保存个人信息
     */
    saveProfile: async function () {
        const username = document.getElementById('edit-username')?.value.trim();
        const email = document.getElementById('edit-email')?.value.trim();
        const oldPassword = document.getElementById('edit-old-password')?.value.trim();
        const newPassword = document.getElementById('edit-password')?.value.trim();
        const confirmPassword = document.getElementById('edit-confirm-password')?.value.trim();

        if (!username) {
            alert('请输入用户名');
            return;
        }

        if (!email) {
            alert('请输入邮箱');
            return;
        }

        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(email)) {
            alert('请输入有效的邮箱地址');
            return;
        }

        if (newPassword) {
            if (!this.oldPasswordVerified) {
                alert('请先输入正确的旧密码');
                return;
            }
            if (newPassword !== confirmPassword) {
                const confirmError = document.getElementById('confirm-password-error');
                if (confirmError) confirmError.textContent = '两次输入的密码不一致！';
                return;
            }
            if (newPassword.length < 6) {
                alert('新密码长度至少为6位');
                return;
            }
        }

        const userInfo = StorageUtil.getItem('userInfo');
        if (!userInfo) return;

        try {
            const response = await fetch('/api/user/update-profile', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    parent_id: userInfo.parent_id,
                    username: username,
                    email: email,
                    old_password: oldPassword,
                    password: newPassword
                })
            });

            const result = await response.json();

            if (result.success) {
                alert('个人信息更新成功');
                this.loadProfileInfo();
                this.cancelEdit();
            } else {
                alert(result.error?.message || result.error || '更新失败');
            }
        } catch (err) {
            console.error('更新个人信息失败:', err);
            alert('更新失败，请稍后再试');
        }
    },

    /**
     * 上传头像
     */
    uploadAvatar: async function (event) {
        const file = event.target.files[0];
        if (!file) return;

        const userInfo = StorageUtil.getItem('userInfo');
        if (!userInfo) return;

        const formData = new FormData();
        formData.append('avatar', file);
        formData.append('parent_id', userInfo.parent_id);

        try {
            const response = await fetch('/api/user/avatar', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();
            
            if (result.success) {
                const data = result.data || result;
                const avatarElement = document.getElementById('modal-avatar');
                if (avatarElement && data.avatar_url) {
                    avatarElement.innerHTML = `<img src="${data.avatar_url}" alt="头像">`;
                }
                
                // 更新本地存储中的头像URL
                userInfo.avatar = data.avatar_url;
                StorageUtil.setItem('userInfo', userInfo);

                // 更新侧边栏头像
                const sidebarAvatar = document.querySelector('.user-avatar-sidebar');
                if (sidebarAvatar && data.avatar_url) {
                    sidebarAvatar.innerHTML = `<img src="${data.avatar_url}" alt="用户头像" style="width: 100%; height: 100%; object-fit: cover;">`;
                }

                alert('头像上传成功');
            } else {
                alert(result.error?.message || '头像上传失败');
            }
        } catch (err) {
            console.error('上传头像失败:', err);
            alert('上传失败，请稍后再试');
        }
    },

    /**
     * 切换到儿童模式
     */
    switchToChildMode: function () {
        const userInfo = StorageUtil.getItem('userInfo');
        if (!userInfo) {
            window.location.href = 'login.html';
            return;
        }

        if (!userInfo.children || userInfo.children.length === 0) {
            alert('请先添加儿童信息');
            window.location.href = 'child-document.html';
            return;
        }

        UserStateUtil.switchToChildMode(userInfo.children[0].id, userInfo.children[0].name);
        window.location.href = 'child-home.html';
    },

    /**
     * 退出登录
     */
    logout: function () {
        StorageUtil.removeItem('userInfo');
        window.location.href = 'login.html';
    },

    /**
     * 检查登录状态
     */
    checkAuth: function () {
        const userInfo = StorageUtil.getItem('userInfo');
        if (!userInfo || (userInfo.mode !== 'parent' && userInfo.role !== 'parent' && userInfo.role !== 'admin')) {
            window.location.href = 'login.html';
            return null;
        }
        return userInfo;
    },

    // 旧密码验证状态
    oldPasswordVerified: false
};

// 添加弹窗相关样式
const profileModalStyles = `
    .profile-modal-content {
        min-height: 200px;
        max-height: 90vh;
    }

    .profile-header {
        display: flex;
        align-items: center;
        gap: 30px;
        margin-bottom: 30px;
    }

    .avatar-section {
        position: relative;
        display: flex;
        flex-direction: column;
        align-items: center;
    }

    .avatar-large {
        width: 100px;
        height: 100px;
        border-radius: 50%;
        background: linear-gradient(145deg, #667eea 0%, #764ba2 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 40px;
        color: white;
        font-weight: 600;
        cursor: pointer;
        position: relative;
        overflow: hidden;
        transition: all 0.3s ease;
    }

    .avatar-large:hover {
        transform: scale(1.05);
    }

    .avatar-large img {
        width: 100%;
        height: 100%;
        object-fit: cover;
    }

    .avatar-upload-hint {
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
        background: rgba(0, 0, 0, 0.7);
        color: white;
        font-size: 12px;
        padding: 4px;
        text-align: center;
        opacity: 0;
        transition: opacity 0.3s ease;
    }

    .avatar-large:hover .avatar-upload-hint {
        opacity: 1;
    }

    #modal-avatar-input {
        display: none;
    }

    .profile-info {
        flex: 1;
    }

    .profile-username {
        font-size: 25px;
        font-weight: 600;
        color: #333;
        margin-bottom: 8px;
        padding-bottom: 8px;
        border-bottom: 2px solid #e8e8e8;
        width: 100%;
    }

    .profile-meta {
        display: flex;
        flex-direction: column;
        gap: 10px;
    }

    .profile-meta-item {
        font-size: 16px;
        color: #999;
    }

    .profile-meta-item span {
        color: #667eea;
        font-weight: 500;
    }

    .profile-actions-outside {
        margin-top: 20px;
        text-align: center;
    }

    .edit-btn {
        padding: 12px 24px;
        font-size: 16px;
        font-weight: 600;
        color: #fff;
        background: linear-gradient(135deg, #773ada 0%, #451594 100%);
        border: none;
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.3s ease;
    }

    .edit-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
    }

    .edit-profile-section {
        margin: 25px 0;
        padding: 20px;
        background: #E8E7FD;
        border-radius: 12px;
        border: 2px solid #e8e8e8;
    }

    .edit-profile-section h4 {
        margin: 0 0 20px 0;
        color: #271151;
        font-size: 18px;
        font-weight: 600;
    }

    .edit-form {
        display: flex;
        flex-direction: column;
        gap: 15px;
    }

    .form-actions {
        display: flex;
        gap: 10px;
        margin-top: 10px;
    }

    .form-actions button {
        flex: 1;
    }
`;

// 保存原始的getStyles方法
ParentComponents._originalGetStyles = ParentComponents.getStyles;

// 将弹窗样式添加到组件库
ParentComponents.getStyles = function () {
    return this._originalGetStyles() + profileModalStyles;
};

