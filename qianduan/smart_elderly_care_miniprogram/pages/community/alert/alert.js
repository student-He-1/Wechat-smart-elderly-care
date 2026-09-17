// community/alert.js
const alertApi = require('../../../services/alert-api.js');

Page({
  data: { alerts: [] },
  onShow() { this.load(); },
  load() {
    const local = wx.getStorageSync('alerts') || [];
    this.setData({ alerts: local });
    alertApi.loadAlerts().then((merged) => {
      wx.setStorageSync('alerts', merged);
      this.setData({ alerts: merged });
    });
  },
  mark(e) {
    const { s } = e.currentTarget.dataset;
    wx.showToast({ title: s, icon: 'success' });
  },
  markDone(e) {
    const id = e.currentTarget.dataset.id;
    const alerts = wx.getStorageSync('alerts') || [];
    const target = alerts.find(x => x.id === id);
    const apply = () => {
      const list = (wx.getStorageSync('alerts') || []).map(a => a.id === id ? { ...a, handled: true } : a);
      wx.setStorageSync('alerts', list);
      this.setData({ alerts: list });
    };
    alertApi.handleServerAlert(target).then(apply).catch(apply);
  },
  previewShot(e) {
    const url = e.currentTarget.dataset.url;
    if (!url) return;
    const urls = (wx.getStorageSync('alerts') || []).map(a => a.snapshotUrl).filter(Boolean);
    wx.previewImage({ current: url, urls: urls.length ? urls : [url] });
  },
  goHome() { wx.reLaunch({ url: '/pages/community/home/home' }); },
  goElders() { wx.reLaunch({ url: '/pages/community/elders/elders' }); },
  goMine() { wx.reLaunch({ url: '/pages/community/mine/mine' }); }
});
