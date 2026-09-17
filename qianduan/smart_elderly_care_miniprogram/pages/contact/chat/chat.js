// contact/chat.js
Page({
  data: {
    targetName: '',
    targetPhone: '',
    target: 'daughter',
    input: '',
    messages: [],
    lastMsgId: ''
  },

  onLoad(opt) {
    this.setData({
      targetName: opt.name || '家人',
      targetPhone: opt.phone || '',
      target: opt.target || 'daughter'
    });
    wx.setNavigationBarTitle({ title: this.data.targetName });
    this.loadMessages();
  },

  loadMessages() {
    const all = wx.getStorageSync('messages') || [];
    this.setData({ messages: all.filter(m => m.channel === 'family' && m.to === this.data.target) });
  },

  onInput(e) { this.setData({ input: e.detail.value }); },

  send() {
    const text = this.data.input.trim();
    if (!text) return;

    const msg = {
      id: 'm' + Date.now(),
      from: 'parent',
      to: this.data.target,
      channel: 'family',
      text,
      time: this.formatTime(new Date())
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
  },

  formatTime(d) {
    const h = String(d.getHours()).padStart(2, '0');
    const m = String(d.getMinutes()).padStart(2, '0');
    return `${h}:${m}`;
  }
});
