// daughter/alerts.js
const alertApi = require('../../../services/alert-api.js');

Page({
  data: {
    tab: 'alerts',
    all: [],
    filtered: []
  },

  goHome() { wx.reLaunch({ url: '/pages/daughter/home/home' }); },
  goAlerts() { wx.reLaunch({ url: '/pages/daughter/alerts/alerts' }); },
  goServices() { wx.reLaunch({ url: '/pages/daughter/services/services' }); },
  goMine() { wx.reLaunch({ url: '/pages/daughter/mine/mine' }); },

  onShow() {
    this.refresh();
  },

  refresh() {
    const fallback = [
      { id: 1, title: '妈妈按下了紧急求助', time: '今天 09:32', level: 'urgent', handled: false },
      { id: 2, title: '降压药 18:00 未确认服用', time: '昨天 18:15', level: 'normal', handled: true }
    ];
    // 先本地兜底渲染，再拉后端合并
    const local = wx.getStorageSync('alerts');
    this._render(local && local.length ? local : fallback);
    alertApi.loadAlerts().then((merged) => {
      wx.setStorageSync('alerts', merged);
      this._render(merged);
    });
  },

  _render(all) {
    this.setData({ all }, () => this.applyFilter());
  },

  switchTab(e) {
    this.setData({ tab: e.currentTarget.dataset.tab }, () => this.applyFilter());
  },

  applyFilter() {
    const { tab, all } = this.data;
    let filtered;
    if (tab === 'unhandled') filtered = all.filter(a => !a.handled);
    else if (tab === 'handled') filtered = all.filter(a => a.handled);
    else filtered = all;
    this.setData({ filtered });
  },

  handleOne(e) {
    const id = e.currentTarget.dataset.id;
    const target = this.data.all.find(a => a.id === id);
    const apply = () => {
      const all = this.data.all.map(a => a.id === id ? { ...a, handled: true } : a);
      wx.setStorageSync('alerts', all);
      this._render(all);
      wx.showToast({ title: '已处理', icon: 'success' });
    };
    // 后端真实告警先调接口标记处理，本地项直接更新
    alertApi.handleServerAlert(target).then(apply).catch(apply);
  },

  // 点整条告警：有现场图看大图，没图看详情
  openAlert(e) {
    const id = e.currentTarget.dataset.id;
    const item = this.data.all.find(a => a.id === id);
    if (!item) return;
    if (item.snapshotUrl) {
      const urls = this.data.all.map(a => a.snapshotUrl).filter(Boolean);
      wx.previewImage({ current: item.snapshotUrl, urls: urls.length ? urls : [item.snapshotUrl] });
    } else {
      wx.showModal({
        title: item.title,
        content: `${item.time}\n状态：${item.handled ? '已处理' : '未处理'}`,
        showCancel: false
      });
    }
  },

  previewShot(e) {
    const url = e.currentTarget.dataset.url;
    if (!url) return;
    const urls = this.data.all.map(a => a.snapshotUrl).filter(Boolean);
    wx.previewImage({ current: url, urls: urls.length ? urls : [url] });
  }
});
