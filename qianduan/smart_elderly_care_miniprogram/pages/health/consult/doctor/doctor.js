// health/consult/doctor.js
Page({
  data: {
    docName: '医生',
    docAvatar: '',
    input: '',
    msgs: [],
    lastId: '',
    quickQs: ['血压偏高怎么办', '吃药忘了怎么办', '头晕要看什么科', '失眠怎么调理']
  },

  onLoad(opt) {
    this.setData({ docName: opt.name || '医生', docAvatar: decodeURIComponent(opt.avatar || '') });
    wx.setNavigationBarTitle({ title: this.data.docName });
  },

  onInput(e) { this.setData({ input: e.detail.value }); },

  askQuick(e) {
    this.sendText(e.currentTarget.dataset.q);
  },

  send() {
    const t = this.data.input.trim();
    if (!t) return;
    this.setData({ input: '' });
    this.sendText(t);
  },

  sendText(text) {
    const myId = 'm' + Date.now();
    this.setData({
      msgs: this.data.msgs.concat({ id: myId, from: 'me', text }),
      lastId: myId
    });
    // 医生延迟回复
    setTimeout(() => {
      const reply = this.autoReply(text);
      const docId = 'd' + Date.now();
      this.setData({
        msgs: this.data.msgs.concat({ id: docId, from: 'doc', text: reply }),
        lastId: docId
      });
    }, 800);
  },

  autoReply(text) {
    if (text.includes('血压') || text.includes('头晕')) {
      return '血压偏高时建议先休息10分钟再测量一次。如果收缩压持续高于140，请按时服药并联系您的社区医生。';
    }
    if (text.includes('药') || text.includes('忘了')) {
      return '如果想起来时离下一次服药还有2小时以上，可以补服；如果快到下一次服药时间了，就跳过这次，不要加倍。';
    }
    if (text.includes('失眠') || text.includes('睡')) {
      return '建议睡前1小时不看手机，卧室保持黑暗安静。如果持续失眠超过2周，建议到神经内科就诊。';
    }
    if (text.includes('发烧') || text.includes('感冒')) {
      return '体温38.5度以下先物理降温，多喝水休息。如果超过3天不退或伴有其他症状，请及时就医。';
    }
    return '您好，您的问题我已记录。建议您详细描述症状的持续时间和伴随表现，必要时到医院面诊。';
  }
});
