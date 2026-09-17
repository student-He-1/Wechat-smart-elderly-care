// community/order-detail.js
const { ORDERS } = require('../../../services/orders.js');

Page({
  data: { order: {} },

  onLoad(opt) {
    const id = opt.id;
    let order = ORDERS.find(o => o.id === id);
    if (!order) {
      // 紧急 SOS 工单
      const alerts = wx.getStorageSync('alerts') || [];
      const a = alerts.find(x => x.id === id);
      if (a) {
        order = {
          id: a.id, elderName: '张奶奶', elderPhone: '138****1234',
          serviceType: 'SOS 紧急求助', bookTime: a.time,
          address: '南开区鼓楼西街 12 号', status: 'pending'
        };
      }
    }
    this.setData({ order: order || {} });
  },

  accept() {
    this.setData({ 'order.status': 'ontheway' });
    wx.showToast({ title: '已接单，出发', icon: 'success' });
  },

  arrive() {
    this.setData({ 'order.status': 'serving' });
    wx.showToast({ title: '开始服务', icon: 'success' });
  },

  finish() {
    this.setData({ 'order.status': 'done' });
    const alerts = wx.getStorageSync('alerts') || [];
    const idx = alerts.findIndex(a => a.id === this.data.order.id);
    if (idx >= 0) alerts[idx].handled = true;
    // 写服务完成通知，子女端 onShow 能读到
    const now = new Date();
    alerts.push({
      id: 'svc-' + Date.now(),
      title: `服务完成：${this.data.order.serviceType}（${this.data.order.elderName}）`,
      time: `今天 ${String(now.getHours()).padStart(2,'0')}:${String(now.getMinutes()).padStart(2,'0')}`,
      level: 'normal',
      handled: false
    });
    wx.setStorageSync('alerts', alerts);
    // 同时写一条消息到 messages，老人端未读提示能看到
    const msgs = wx.getStorageSync('messages') || [];
    msgs.push({
      id: 'm' + Date.now(),
      from: 'community',
      channel: 'notice',
      text: `您好，您预约的${this.data.order.serviceType}已完成，感谢您的配合。`,
      time: `今天 ${String(now.getHours()).padStart(2,'0')}:${String(now.getMinutes()).padStart(2,'0')}`
    });
    wx.setStorageSync('messages', msgs);
    wx.showModal({
      title: '服务完成',
      content: '已通知老人和子女',
      showCancel: false,
      success: () => wx.navigateBack()
    });
  }
});
