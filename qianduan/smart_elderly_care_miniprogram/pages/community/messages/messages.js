// community/messages.js —— 老人留言聊天页
Page({
  data: { input: '', list: [], lastId: '' },

  onShow() { this.load(); },

  load() {
    const all = wx.getStorageSync('messages') || [];
    this.setData({ list: all.filter(m => m.channel === 'worker') });
  },

  onInput(e) { this.setData({ input: e.detail.value }); },

  send() {
    const text = this.data.input.trim();
    if (!text) return;
    const now = new Date();
    const msg = {
      id: 'm' + Date.now(),
      from: 'community',
      channel: 'worker',
      text,
      time: `${String(now.getHours()).padStart(2,'0')}:${String(now.getMinutes()).padStart(2,'0')}`
    };
    const all = wx.getStorageSync('messages') || [];
    all.push(msg);
    wx.setStorageSync('messages', all);
    this.setData({
      input: '',
      list: this.data.list.concat(msg),
      lastId: 'm-' + msg.id
    });
    wx.showToast({ title: '已发送', icon: 'success' });
  }
});
