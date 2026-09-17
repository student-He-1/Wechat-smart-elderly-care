// community/home.js
const { ORDERS } = require('../../../services/orders.js');
const alertApi = require('../../../services/alert-api.js');

const URGENT_TYPE_TEXT = { fall: '跌倒告警', sos: 'SOS 紧急求助' };

Page({
  data: {
    dark: false,
    tab: 'pending',
    all: ORDERS,
    filtered: [],
    counts: { pending: 0, active: 0, done: 0 },
    urgentCount: 0,
    statusText: { pending: '待接单', ontheway: '已出发', serving: '服务中', done: '已完成' }
  },

  onShow() {
    this.setData({ dark: wx.getStorageSync('dark') });
    this.refresh();
  },

  refresh() {
    this._build(wx.getStorageSync('alerts') || []);
    // 异步合并后端真实告警（跌倒/SOS）
    alertApi.loadAlerts().then((merged) => {
      wx.setStorageSync('alerts', merged);
      this._build(merged);
    });
  },

  _build(alerts) {
    // 未处理的紧急告警作为置顶紧急工单
    const urgent = alerts.filter(a => !a.handled && a.level === 'urgent').map(a => ({
      id: a.id,
      elderName: '张奶奶',
      serviceType: URGENT_TYPE_TEXT[a.type] || 'SOS 紧急求助',
      bookTime: a.time,
      address: '南开区鼓楼西街 12 号',
      status: 'pending',
      urgent: true
    }));

    const all = urgent.concat(ORDERS);
    const counts = {
      pending: all.filter(o => o.status === 'pending').length,
      active: all.filter(o => o.status === 'ontheway' || o.status === 'serving').length,
      done: all.filter(o => o.status === 'done').length
    };

    this.setData({
      all,
      counts,
      urgentCount: urgent.length
    }, () => this.applyFilter());
  },

  applyFilter() {
    const t = this.data.tab;
    let filtered;
    if (t === 'pending') filtered = this.data.all.filter(o => o.status === 'pending');
    else if (t === 'active') filtered = this.data.all.filter(o => o.status === 'ontheway' || o.status === 'serving');
    else filtered = this.data.all.filter(o => o.status === 'done');
    this.setData({ filtered });
  },

  setTab(e) {
    this.setData({ tab: e.currentTarget.dataset.t }, () => this.applyFilter());
  },

  openOrder(e) {
    const id = e.currentTarget.dataset.id;
    wx.navigateTo({ url: '/pages/community/order-detail/order-detail?id=' + id });
  },

  goAlert() { wx.reLaunch({ url: '/pages/community/alert/alert' }); },
  goElders() { wx.reLaunch({ url: '/pages/community/elders/elders' }); },
  goMine() { wx.reLaunch({ url: '/pages/community/mine/mine' }); },

  goRules() { wx.navigateTo({ url: '/pages/community/rules/rules' }); },
  goVisit() { wx.navigateTo({ url: '/pages/community/visit/visit' }); },
  goEvaluation() { wx.navigateTo({ url: '/pages/community/evaluation/evaluation' }); },
  goMessages() { wx.navigateTo({ url: '/pages/community/messages/messages' }); }
});
