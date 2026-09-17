// daughter/chat.js
Page({
  data: {
    input: '',
    messages: [],
    lastMsgId: ''
  },

  onShow() {
    this.loadMessages();
  },

  loadMessages() {
    const all = wx.getStorageSync('messages') || [];
    this.setData({ messages: all.filter(m => m.channel === 'family' && m.to === 'daughter') });
  },

  onInput(e) { this.setData({ input: e.detail.value }); },

  send() {
    const text = this.data.input.trim();
    if (!text) return;
    const now = new Date();
    const msg = {
      id: 'm' + Date.now(),
      from: 'daughter',
      channel: 'family',
      text,
      time: `${String(now.getHours()).padStart(2,'0')}:${String(now.getMinutes()).padStart(2,'0')}`
    };
    const all = wx.getStorageSync('messages') || [];
    all.push(msg);
    wx.setStorageSync('messages', all);
    this.setData({
      input: '',
      messages: this.data.messages.concat(msg),
      lastMsgId: 'msg-' + msg.id
    });
    wx.showToast({ title: '已发送', icon: 'success' });
  }
});
