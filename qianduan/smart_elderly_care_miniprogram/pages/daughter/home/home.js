// daughter/home.js —— 子女端首页
const { NEWS } = require('../../../services/news.js');
const alertApi = require('../../../services/alert-api.js');
const { BASE_URL } = require('../../../utils/config');
// 主后端提醒 WebSocket（跌倒/SOS 实时推送）
const REMINDER_WS = BASE_URL.replace(/^http/, 'ws').replace(/\/api$/, '') + '/ws/reminders';

Page({
  data: {
    dark: false,
    status: {
      medicineDone: 2,
      medicineTotal: 3,
      bp: '138/86',
      lastActive: '10 分钟前',
      alert: false
    },
    alerts: [],
    news: NEWS.slice(0, 3),
    latestMsg: '',
    latestMsgTime: ''
  },

  onShow() {
    this.setData({ dark: wx.getStorageSync('dark') });
    this.loadAlerts();
    this.connectReminder();
    const msgs = wx.getStorageSync('messages') || [];
    if (msgs.length > 0) {
      const last = msgs[msgs.length - 1];
      this.setData({ latestMsg: last.text, latestMsgTime: last.time });
    }
  },

  onHide() {
    // 离开首页（如进监控页）关闭 socket，避免与监控页的 5002 socket 冲突
    this.closeReminder();
  },

  onUnload() {
    this.closeReminder();
  },

  connectReminder() {
    const that = this;
    this.closeReminder(true);
    wx.onSocketMessage((res) => {
      try {
        const d = JSON.parse(res.data);
        if (d.type === 'alert') that.onFallPush(d);
      } catch (e) {}
    });
    // 错峰：等监控页推流 socket 关闭后再连，避免全局单 socket 抢占
    if (this._reminderTimer) clearTimeout(this._reminderTimer);
    this._reminderTimer = setTimeout(() => {
      try {
        wx.connectSocket({ url: REMINDER_WS, complete: () => {} });
      } catch (e) {}
    }, 300);
  },

  closeReminder(silent) {
    if (this._reminderTimer) { clearTimeout(this._reminderTimer); this._reminderTimer = null; }
    try { wx.offSocketMessage && wx.offSocketMessage(); } catch (e) {}
    try { wx.closeSocket({ complete: () => {} }); } catch (e) {}
  },

  onFallPush(d) {
    wx.vibrateShort && wx.vibrateShort({ type: 'medium' });
    this.loadAlerts();
    wx.showModal({
      title: '老人异常告警',
      content: d.message || '检测到老人可能跌倒，请立即查看',
      confirmText: '查看监控',
      cancelText: '稍后',
      success: (r) => {
        if (r.confirm) wx.navigateTo({ url: '/pages/monitor/monitor' });
      }
    });
  },

  loadAlerts() {
    // 先用本地立即渲染，再异步合并后端真实告警（跌倒/SOS）
    const local = wx.getStorageSync('alerts') || [];
    this._applyAlerts(local);
    alertApi.loadAlerts().then((merged) => {
      // 同步写一份到 storage，供告警页复用
      wx.setStorageSync('alerts', merged);
      this._applyAlerts(merged);
    });
  },

  _applyAlerts(alerts) {
    const hasAlert = alerts.some(a => a.level === 'urgent' && !a.handled);
    this.setData({
      alerts: alerts.filter(a => !a.handled),
      'status.alert': hasAlert
    });
  },

  backToParent() {
    wx.setStorageSync('role', 'parent');
    wx.reLaunch({ url: '/pages/index/index' });
  },

  goMonitor() {
    wx.navigateTo({ url: '/pages/monitor/monitor' });
  },

  goDetail() {
    wx.navigateTo({ url: '/pages/daughter/detail/detail' });
  },

  goAlerts() {
    wx.reLaunch({ url: '/pages/daughter/alerts/alerts' });
  },

  goMine() {
    wx.reLaunch({ url: '/pages/daughter/mine/mine' });
  },

  goServices() {
    wx.reLaunch({ url: '/pages/daughter/services/services' });
  },

  goNewsList() {
    wx.navigateTo({ url: '/pages/news/index' });
  },

  goMessages() {
    wx.navigateTo({ url: '/pages/daughter/chat/chat' });
  },

  openNews(e) {
    wx.navigateTo({ url: '/pages/news/detail/detail?id=' + e.currentTarget.dataset.id });
  },

  callMom() {
    wx.showModal({
      title: '拨打妈妈电话',
      content: '确定要拨打 138****8888 吗？',
      confirmText: '拨打',
      success: (res) => {
        if (res.confirm) {
          wx.makePhoneCall({ phoneNumber: '13800138000' });
        }
      }
    });
  },

  goHealthAssistant() {
    wx.navigateTo({ url: '/pages/health/assistant/assistant' });
  },

  handleAlert(e) {
    const id = e.currentTarget.dataset.id;
    const target = this.data.alerts.find(a => a.id === id);
    const done = () => {
      wx.showToast({ title: '已标记处理', icon: 'success' });
      this.loadAlerts();   // 重新拉后端，已处理的告警消失、状态恢复正常
    };
    // 后端真实告警调接口标记；本地项直接更新后刷新
    if (target && target.serverId) {
      alertApi.handleServerAlert(target).then(done).catch(done);
    } else {
      const all = (wx.getStorageSync('alerts') || []).map(a => a.id === id ? { ...a, handled: true } : a);
      wx.setStorageSync('alerts', all);
      done();
    }
  },

  showDemo() {
    wx.showToast({ title: '演示功能', icon: 'none' });
  }
});
