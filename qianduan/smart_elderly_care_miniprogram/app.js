// app.js
// 全局注入夜间模式：每个页面 onShow 自动读 storage dark
const __Page = Page;
Page = function(options) {
  const origOnShow = options.onShow;
  options.onShow = function() {
    this.setData({ dark: !!wx.getStorageSync('dark') });
    if (origOnShow) origOnShow.call(this);
  };
  __Page(options);
};

App({
  onLaunch() {
    // 展示本地存储能力
    const logs = wx.getStorageSync('logs') || []
    logs.unshift(Date.now())
    wx.setStorageSync('logs', logs)

    // 初始化API配置
    this.globalData.apiBaseUrl = 'http://192.168.190.11:8000/api'
  },
  globalData: {
    userInfo: null,
    apiBaseUrl: '',
    // 系统配置
    systemConfig: {
      appName: '智慧养老系统',
      version: '1.0.0',
      themeColor: '#667eea'
    }
  }
})
