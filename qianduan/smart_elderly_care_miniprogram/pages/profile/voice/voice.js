// pages/profile/voice/voice.js
Page({
  data: {
    volume: 80, // 默认音量80%
    voiceEnabled: true // 默认开启语音
  },

  onLoad() {
    console.log('语音设置页面加载');
    this.loadVoiceSettings();
  },

  // 从后端加载语音设置
  loadVoiceSettings() {
    // 这里可以添加从后端加载设置的逻辑
    // 暂时使用默认值
  },

  // 调整音量
  adjustVolume(e) {
    const volume = e.detail.value;
    this.setData({ volume });
  },

  // 切换语音开关
  toggleVoice(e) {
    const voiceEnabled = e.detail.value;
    this.setData({ voiceEnabled });
  },

  // 保存设置
  saveSettings() {
    // 这里可以添加保存设置到后端的逻辑
    wx.showToast({ title: '设置已保存', icon: 'success' });
  }
});