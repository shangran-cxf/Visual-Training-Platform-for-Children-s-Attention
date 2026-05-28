// 存储工具类
class StorageUtil {
  // 获取存储项
  static getItem(key) {
    try {
      const item = localStorage.getItem(key);
      return item ? JSON.parse(item) : null;
    } catch (error) {
      console.error('获取存储项失败:', error);
      return null;
    }
  }

  // 设置存储项
  static setItem(key, value) {
    try {
      localStorage.setItem(key, JSON.stringify(value));
      return true;
    } catch (error) {
      console.error('设置存储项失败:', error);
      return false;
    }
  }

  // 删除存储项
  static removeItem(key) {
    try {
      localStorage.removeItem(key);
      return true;
    } catch (error) {
      console.error('删除存储项失败:', error);
      return false;
    }
  }

  // 清空所有存储项
  static clear() {
    try {
      localStorage.clear();
      return true;
    } catch (error) {
      console.error('清空存储失败:', error);
      return false;
    }
  }
}

// 用户状态管理工具
class UserStateUtil {
  // 检查用户是否已登录
  static isLoggedIn() {
    return StorageUtil.getItem('userInfo') !== null;
  }

  // 获取当前登录的孩子ID
  static getCurrentChildId() {
    return localStorage.getItem('currentChildId');
  }

  // 设置当前登录的孩子ID
  static setCurrentChildId(childId) {
    localStorage.setItem('currentChildId', childId);
  }

  // 从登录响应初始化用户信息
  static initFromLoginResponse(response) {
    const userInfo = {
      parent_id: response.parent_id,
      username: response.username,
      role: response.role,
      avatar: response.avatar || null,
      children: response.children || [],
      mode: 'parent',
      token: response.token,
    };
    StorageUtil.setItem('userInfo', userInfo);
    // 同时保存 token 到 auth_token，方便后续 API 调用
    if (response.token) {
      localStorage.setItem('auth_token', response.token);
    }
    return userInfo;
  }

  // 切换到家长模式
  static switchToParentMode() {
    const userInfo = StorageUtil.getItem('userInfo');
    if (userInfo) {
      userInfo.mode = 'parent';
      StorageUtil.setItem('userInfo', userInfo);
    }
  }

  // 切换到儿童模式
  static switchToChildMode(childId) {
    const userInfo = StorageUtil.getItem('userInfo');
    if (userInfo) {
      userInfo.mode = 'child';
      userInfo.currentChildId = childId;
      StorageUtil.setItem('userInfo', userInfo);
      this.setCurrentChildId(childId);
    }
  }

  // 获取用户信息
  static getUserInfo() {
    return StorageUtil.getItem('userInfo');
  }

  // 登出
  static logout() {
    StorageUtil.removeItem('userInfo');
    localStorage.removeItem('currentChildId');
  }

  // 获取当前孩子的名字
  static getCurrentChildName() {
    const userInfo = StorageUtil.getItem('userInfo');
    const currentChildId = localStorage.getItem('currentChildId');

    if (userInfo && userInfo.children && currentChildId) {
      const child = userInfo.children.find((c) => c.id == currentChildId);
      return child ? child.name : '';
    }
    return '';
  }
}

// 勋章工具类
class MedalUtil {
  static _defaultMedalsCache = null;

  static getDefaultMedals() {
    if (this._defaultMedalsCache === null) {
      this._defaultMedalsCache = [
        {
          id: 1,
          name: '太空小达人',
          howto: '成功完成太空小火箭所有难度关卡',
          gameId: 'game1',
          image: 'medal-image/game1.png',
          completedLevels: 0,
          totalLevels: 3,
          unlocked: false,
        },
        {
          id: 2,
          name: '垃圾小助手',
          howto: '成功完成垃圾小卫士所有难度关卡',
          gameId: 'game2',
          image: 'medal-image/game2.png',
          completedLevels: 0,
          totalLevels: 3,
          unlocked: false,
        },
        {
          id: 3,
          name: '魔法冒险家',
          howto: '成功完成魔法迷宫所有难度关卡',
          gameId: 'game3',
          image: 'medal-image/game3.png',
          completedLevels: 0,
          totalLevels: 3,
          unlocked: false,
        },
        {
          id: 4,
          name: '植物守护者',
          howto: '成功完成植物浇水所有难度关卡',
          gameId: 'game4',
          image: 'medal-image/game4.png',
          completedLevels: 0,
          totalLevels: 3,
          unlocked: false,
        },
        {
          id: 5,
          name: '太阳追踪者',
          howto: '成功完成追太阳所有难度关卡',
          gameId: 'game5',
          image: 'medal-image/game5.png',
          completedLevels: 0,
          totalLevels: 3,
          unlocked: false,
        },
        {
          id: 6,
          name: '动物追踪员',
          howto: '成功完成森林小动物追踪所有难度关卡',
          gameId: 'game6',
          image: 'medal-image/game6.png',
          completedLevels: 0,
          totalLevels: 3,
          unlocked: false,
        },
        {
          id: 7,
          name: '金牌甜品销售员',
          howto: '成功完成甜品店小帮工所有难度关卡',
          gameId: 'game7',
          image: 'medal-image/game7.png',
          completedLevels: 0,
          totalLevels: 3,
          unlocked: false,
        },
        {
          id: 8,
          name: '海底捉迷藏大师',
          howto: '成功完成海底捉迷藏所有难度关卡',
          gameId: 'game8',
          image: 'medal-image/game8.png',
          completedLevels: 0,
          totalLevels: 3,
          unlocked: false,
        },
        {
          id: 9,
          name: '分类小能手',
          howto: '成功完成环保小卫士所有难度关卡',
          gameId: 'game9',
          image: 'medal-image/game9.png',
          completedLevels: 0,
          totalLevels: 3,
          unlocked: false,
        },
        {
          id: 10,
          name: '冰雪信使',
          howto: '成功完成冰雪王国小邮差所有难度关卡',
          gameId: 'game10',
          image: 'medal-image/game10.png',
          completedLevels: 0,
          totalLevels: 3,
          unlocked: false,
        },
        {
          id: 11,
          name: '打卡小新星',
          howto: '连续打卡3天',
          type: 'checkin',
          image: 'medal-image/3day.png',
          days: 0,
          required: 3,
          unlocked: false,
        },
        {
          id: 12,
          name: '坚持小勇士',
          howto: '连续打卡7天',
          type: 'checkin',
          image: 'medal-image/7day.png',
          days: 0,
          required: 7,
          unlocked: false,
        },
        {
          id: 13,
          name: '专注小达人',
          howto: '连续打卡14天',
          type: 'checkin',
          image: 'medal-image/14day.png',
          days: 0,
          required: 14,
          unlocked: false,
        },
        {
          id: 14,
          name: '自律小榜样',
          howto: '连续打卡30天',
          type: 'checkin',
          image: 'medal-image/30day.png',
          days: 0,
          required: 30,
          unlocked: false,
        },
        {
          id: 15,
          name: '毅力小冠军',
          howto: '连续打卡60天',
          type: 'checkin',
          image: 'medal-image/60day.png',
          days: 0,
          required: 60,
          unlocked: false,
        },
      ];
    }
    // 返回缓存的深拷贝，防止外部修改缓存
    return JSON.parse(JSON.stringify(this._defaultMedalsCache));
  }

  static getCurrentChildId() {
    return UserStateUtil.getCurrentChildId();
  }

  static getStorageKey(childId) {
    return `medals_${childId}`;
  }

  static getCheckinDateKey(childId) {
    return `lastCheckin_${childId}`;
  }

  static getCheckinStreakKey(childId) {
    return `checkinStreak_${childId}`;
  }

  static loadMedals(childId = this.getCurrentChildId()) {
    if (!childId) return this.getDefaultMedals();

    const medals = this.getDefaultMedals();
    const savedData = localStorage.getItem(this.getStorageKey(childId));
    if (!savedData) return medals;

    try {
      const savedMedals = JSON.parse(savedData);
      medals.forEach((medal) => {
        const savedMedal = savedMedals.find((item) => item.id === medal.id);
        if (savedMedal) Object.assign(medal, savedMedal);
      });
    } catch (error) {
      console.error('加载勋章数据失败:', error);
    }

    return medals;
  }

  static saveMedals(medals, childId = this.getCurrentChildId()) {
    if (!childId) return false;
    try {
      localStorage.setItem(this.getStorageKey(childId), JSON.stringify(medals));
      return true;
    } catch (error) {
      console.error('保存勋章数据失败:', error);
      return false;
    }
  }

  static getDifficultyLevel(level, fallbackLevel = 1) {
    const levelMap = {
      easy: 1,
      medium: 2,
      hard: 3,
    };

    if (typeof level === 'number' && Number.isFinite(level)) {
      return Math.max(1, Math.min(3, Math.floor(level)));
    }

    if (typeof level === 'string') {
      const normalized = level.trim().toLowerCase();
      if (levelMap[normalized]) return levelMap[normalized];

      const parsed = Number.parseInt(normalized, 10);
      if (Number.isFinite(parsed)) {
        return Math.max(1, Math.min(3, parsed));
      }
    }

    return Math.max(1, Math.min(3, fallbackLevel));
  }

  static getMedalByGameId(gameId, medals) {
    return medals.find((medal) => medal.gameId === gameId);
  }

  static getMedalById(medalId, medals) {
    return medals.find((medal) => medal.id === medalId);
  }

  static unlockMedal(medal, medals, childId, shouldNotify = true) {
    if (!medal || medal.unlocked) return null;

    medal.unlocked = true;
    this.saveMedals(medals, childId);

    if (shouldNotify) {
      this.showUnlockNotification(medal);
    }

    return medal;
  }

  static recordGameProgress(gameId, level, options = {}) {
    const childId = options.childId || this.getCurrentChildId();
    if (!childId) return null;

    const medals = this.loadMedals(childId);
    const medal = this.getMedalByGameId(gameId, medals);
    if (!medal) return null;

    const currentCompleted = Number.isFinite(medal.completedLevels) ? medal.completedLevels : 0;
    let nextCompleted = currentCompleted;

    if (options.increment) {
      nextCompleted = Math.min(medal.totalLevels || 3, currentCompleted + 1);
    } else {
      nextCompleted = Math.max(currentCompleted, this.getDifficultyLevel(level, currentCompleted));
    }

    medal.completedLevels = nextCompleted;
    const justUnlocked = !medal.unlocked && medal.completedLevels >= medal.totalLevels;

    if (justUnlocked) {
      this.unlockMedal(medal, medals, childId, options.notify !== false);
    } else {
      this.saveMedals(medals, childId);
    }

    return {
      medal,
      justUnlocked,
      medals,
    };
  }

  static syncCheckinProgress(childId = this.getCurrentChildId(), shouldNotify = true) {
    if (!childId) return [];

    const medals = this.loadMedals(childId);
    const streak = Number.parseInt(localStorage.getItem(this.getCheckinStreakKey(childId)) || '0', 10) || 0;
    const unlockedMedals = [];

    medals.forEach((medal) => {
      if (medal.type !== 'checkin') return;

      medal.days = streak;
      if (!medal.unlocked && medal.days >= medal.required) {
        medal.unlocked = true;
        unlockedMedals.push(medal);
      }
    });

    this.saveMedals(medals, childId);

    if (shouldNotify) {
      unlockedMedals.forEach((medal) => this.showUnlockNotification(medal));
    }

    return unlockedMedals;
  }

  static recordCheckin(childId = this.getCurrentChildId(), shouldNotify = true) {
    if (!childId) return null;

    const today = new Date().toDateString();
    const lastCheckin = localStorage.getItem(this.getCheckinDateKey(childId));
    const checkinStreak = Number.parseInt(localStorage.getItem(this.getCheckinStreakKey(childId)) || '0', 10) || 0;

    if (lastCheckin === today) {
      return {
        streak: checkinStreak,
        unlockedMedals: this.syncCheckinProgress(childId, false),
      };
    }

    const yesterday = new Date();
    yesterday.setDate(yesterday.getDate() - 1);
    const newStreak = lastCheckin === yesterday.toDateString() ? checkinStreak + 1 : 1;

    localStorage.setItem(this.getCheckinDateKey(childId), today);
    localStorage.setItem(this.getCheckinStreakKey(childId), String(newStreak));

    return {
      streak: newStreak,
      unlockedMedals: this.syncCheckinProgress(childId, shouldNotify),
    };
  }

  static ensureNotificationStyle() {
    if (document.getElementById('medal-notification-style')) return;

    const style = document.createElement('style');
    style.id = 'medal-notification-style';
    style.textContent = `
      .global-medal-notification {
        position: fixed;
        inset: 0;
        display: flex;
        align-items: center;
        justify-content: center;
        background: rgba(0, 0, 0, 0.28);
        z-index: 9999;
        animation: medalFadeIn 0.25s ease;
      }

      .global-medal-notification-card {
        min-width: 280px;
        max-width: 360px;
        padding: 28px 24px;
        text-align: center;
        border-radius: 28px;
        background: linear-gradient(180deg, #fff7d1 0%, #ffd38b 100%);
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.28);
      }

      .global-medal-notification-card img {
        width: 132px;
        height: 132px;
        object-fit: contain;
        animation: medalUnlockSpin 1.3s ease-in-out;
      }

      .global-medal-notification-title {
        margin-top: 14px;
        font-size: 26px;
        font-weight: 800;
        color: #8a4b12;
      }

      .global-medal-notification-text {
        margin-top: 10px;
        font-size: 20px;
        font-weight: 700;
        color: #3d2a14;
      }

      @keyframes medalFadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
      }

      @keyframes medalUnlockSpin {
        0% { transform: scale(0.65) rotate(0deg); filter: grayscale(100%); opacity: 0.4; }
        55% { transform: scale(1.18) rotate(220deg); filter: grayscale(0%); opacity: 1; }
        100% { transform: scale(1) rotate(360deg); filter: grayscale(0%); opacity: 1; }
      }
    `;

    document.head.appendChild(style);
  }

  static showUnlockNotification(medal) {
    if (!medal || typeof document === 'undefined') return;

    this.ensureNotificationStyle();

    // 确保有正确的图片路径，防止旧缓存数据覆盖了 image
    const defaultMedal = this.getDefaultMedals().find((m) => m.id === medal.id);
    const medalImage = medal.image || (defaultMedal ? defaultMedal.image : 'medal-image/game1.png');

    // 动态判断路径：如果页面在 training 或 detect 等子文件夹中，则加上 ../ 回到 frontend 根目录
    const pathname = window.location.pathname;
    const inSubDir =
      pathname.includes('/training/') || pathname.includes('/detect/') || pathname.includes('/assessment/');
    const imagePath = inSubDir ? `../${medalImage}` : medalImage;

    const overlay = document.createElement('div');
    overlay.className = 'global-medal-notification';
    overlay.innerHTML = `
      <div class="global-medal-notification-card">
        <img src="${imagePath}" alt="${medal.name}">
        <div class="global-medal-notification-title">${medal.name}</div>
        <div class="global-medal-notification-text">恭喜获得${medal.name}</div>
      </div>
    `;

    document.body.appendChild(overlay);
    window.setTimeout(() => overlay.remove(), 2600);
  }
}

// API 配置工具
function getBaseUrl() {
  const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
  return isLocal ? 'http://localhost:5000' : window.location.origin;
}

// HTML 转义函数，防止 XSS 攻击
function escapeHtml(str) {
  if (str === null || str === undefined) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

// 时间工具类 — 将后端 UTC 时间戳转为本地时间显示
class TimeUtil {
  // 将 API 返回的 ISO 字符串或 SQLite 格式转为本地时间 Date 对象
  static parse(isoStr) {
    if (!isoStr) return null;
    // 处理 SQLite 格式 2026-05-28 16:12:00（兼容旧接口）
    if (typeof isoStr === 'string' && isoStr.indexOf(' ') > 0 && isoStr.indexOf('T') === -1) {
      isoStr = isoStr.replace(' ', 'T');
    }
    const d = new Date(isoStr);
    return isNaN(d.getTime()) ? null : d;
  }

  // 显示日期时间：YYYY/M/D HH:mm
  static format(isoStr) {
    const d = TimeUtil.parse(isoStr);
    if (!d) return isoStr || '';
    return `${d.getFullYear()}/${d.getMonth() + 1}/${d.getDate()} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`;
  }

  // 显示日期：YYYY/M/D
  static formatDate(isoStr) {
    const d = TimeUtil.parse(isoStr);
    if (!d) return isoStr || '';
    return `${d.getFullYear()}/${d.getMonth() + 1}/${d.getDate()}`;
  }

  // 获取当前北京时间日期字符串 YYYY-MM-DD（用于 API 查询）
  static todayStr() {
    const now = new Date();
    return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;
  }

  // 相对时间：刚刚 / N分钟前 / N小时前 / N天前
  static relative(isoStr) {
    const d = TimeUtil.parse(isoStr);
    if (!d) return isoStr || '';
    const now = new Date();
    const diff = now - d;
    if (diff < 60000) return '刚刚';
    if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`;
    if (diff < 2592000000) return `${Math.floor(diff / 86400000)}天前`;
    return TimeUtil.format(isoStr);
  }
}

// 导出类
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { UserStateUtil, StorageUtil, MedalUtil, TimeUtil, getBaseUrl };
} else {
  window.UserStateUtil = UserStateUtil;
  window.StorageUtil = StorageUtil;
  window.MedalUtil = MedalUtil;
  window.TimeUtil = TimeUtil;
  window.getBaseUrl = getBaseUrl;
  window.escapeHtml = escapeHtml;
}
