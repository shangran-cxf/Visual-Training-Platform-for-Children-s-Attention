// API 基础地址配置
window.API_BASE_URL = (function() {
  if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    return 'http://localhost:5000';
  }
  var protocol = window.location.protocol;
  var host = window.location.host;
  if (host.includes(':')) {
    return protocol + '//' + host.split(':')[0] + ':5000';
  }
  return protocol + '//' + host;
})();

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
      uid: response.uid,
      username: response.username,
      role: response.role,
      children: response.children || [],
      mode: 'parent',
      token: response.token
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
      const child = userInfo.children.find(c => c.id == currentChildId);
      return child ? child.name : '';
    }
    return '';
  }
}

// 导出类
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { UserStateUtil, StorageUtil };
} else {
  window.UserStateUtil = UserStateUtil;
  window.StorageUtil = StorageUtil;
}
