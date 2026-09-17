// config.js —— 全局配置：后端地址、角色映射（唯一需要改环境的地方）

// 后端 FastAPI 地址（所有 AI/语音/数据接口都在 8000）
// - 微信开发者工具(PC)：用 localhost 即可
// - 真机预览：改成电脑的局域网 IP，例如 'http://192.168.x.x:8000/api'，且手机与电脑同一 WiFi
// 注意：开发者工具需勾选「不校验合法域名、web-view（业务域名）、TLS 版本以及 HTTPS 证书」
const BASE_URL = 'http://localhost:8000/api';

// 前端 role -> 后端身份/用户ID（演示家庭固定三人）
// 前端老人端叫 parent，后端叫 elder
const ROLE_MAP = {
  parent:    { backendRole: 'elder',     userId: 1, name: '张奶奶' },
  elder:     { backendRole: 'elder',     userId: 1, name: '张奶奶' },
  daughter:  { backendRole: 'daughter',  userId: 2, name: '李女士' },
  community: { backendRole: 'community', userId: 3, name: '王师傅' }
};

// 读取当前登录身份，默认老人端
function currentIdentity() {
  const role = wx.getStorageSync('role') || 'parent';
  return ROLE_MAP[role] || ROLE_MAP.parent;
}

module.exports = {
  BASE_URL,
  ROLE_MAP,
  currentIdentity
};
