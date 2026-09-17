// talk.js —— AI 聊天二级页（健康助手接真实后端 Agent；陪伴助手待百炼接入）
const agentApi = require('../../../services/agent-api');

Page({
  data: {
    inputValue: '',
    chatHistory: [],
    isLoading: false,
    isRecording: false,
    recordManager: null,
    sessionId: null,        // 健康助手多轮会话ID
    autoSpeak: true,        // AI 回复后是否用所选方言自动朗读
    dialects: [
      { value: 'mandarin', label: '普通话' },
      { value: 'sichuan', label: '四川话' },
      { value: 'northeast', label: '东北话' }
    ],
    selectedDialectIndex: 0,
    selectedDialect: 'mandarin',
    selectedDialectLabel: '普通话',
    userAvatar: '/assets/images/6-3.png'
  },

  onLoad(options) {
    const type = options.type || 'companion';
    this._audio = wx.createInnerAudioContext();
    this._playingIdx = -1;
    this._paused = false;
    this._audio.onEnded(() => { this._playingIdx = -1; this._paused = false; });
    this._audio.onStop(() => { this._playingIdx = -1; this._paused = false; });
    this._cacheKey = type === 'health' ? null : 'companion_chat_history';
    this.setData({
      assistantType: type,
      navTitle: type === 'health' ? '健康咨询助手' : '陪伴聊天助手'
    });
    wx.setNavigationBarTitle({
      title: type === 'health' ? '健康咨询助手' : '陪伴聊天助手'
    });
    const welcome = type === 'health'
      ? '您好，我是您的健康助手，可以问我吃药、血压、血糖的问题。'
      : '您好，我是您的陪伴助手，想聊点什么？';
    this._welcome = welcome;
    // 陪伴助手：优先恢复本地历史，没有才显示欢迎语
    if (this._cacheKey && this._restoreHistory()) {
      // 已恢复历史，不重复加欢迎语
    } else {
      this.addSystemMessage(welcome);
    }
    this.initRecordManager();
  },

  // 保存对话历史到本地（仅陪伴助手，最多50条）
  _saveHistory() {
    if (!this._cacheKey) return;
    try {
      const history = (this.data.chatHistory || [])
        .filter(m => (m.role === 'user' || m.role === 'assistant') && m.content)
        .slice(-50)
        .map(m => ({ role: m.role, content: m.content }));
      wx.setStorageSync(this._cacheKey, history);
    } catch (e) {
      console.warn('保存陪伴对话历史失败:', e);
    }
  },

  // 从本地恢复对话历史
  _restoreHistory() {
    if (!this._cacheKey) return false;
    try {
      const history = wx.getStorageSync(this._cacheKey);
      if (history && history.length > 0) {
        this.setData({ chatHistory: history });
        return true;
      }
    } catch (e) {
      console.warn('恢复陪伴对话历史失败:', e);
    }
    return false;
  },

  onUnload() {
    if (this._audio) {
      this._audio.destroy();
      this._audio = null;
    }
  },

  initRecordManager() {
    this.setData({ recordManager: wx.getRecorderManager() });
    const recordManager = this.data.recordManager;
    recordManager.onStart(() => console.log('录音开始'));
    recordManager.onStop((res) => {
      console.log('录音结束:', res);
      this.uploadVoice(res.tempFilePath, { size: res.fileSize, duration: res.duration });
    });
    recordManager.onError((err) => {
      console.error('录音错误:', err);
      wx.showToast({ title: '录音失败，请重试', icon: 'none' });
      this.setData({ isRecording: false });
    });
  },

  addSystemMessage(content) {
    this.setData({
      chatHistory: [...this.data.chatHistory, { role: 'assistant', content }]
    });
  },

  bindInput(e) {
    this.setData({ inputValue: e.detail.value });
  },

  toggleSpeak() {
    this.setData({ autoSpeak: !this.data.autoSpeak });
  },

  sendMessage() {
    const message = this.data.inputValue.trim();
    if (!message) {
      wx.showToast({ title: '请输入消息', icon: 'none' });
      return;
    }
    this.setData({ inputValue: '' });
    this.askBackend(message);
  },

  // 统一的后端问答：文字输入和语音识别结果都走这里
  askBackend(question) {
    this.setData({
      chatHistory: [...this.data.chatHistory, { role: 'user', content: question }],
      isLoading: true
    });

    // 陪伴助手：接真实轻量闲聊接口（纯聊天，不挂工具/不查库）
    if (this.data.assistantType !== 'health') {
      const history = this.data.chatHistory
        .filter(m => (m.role === 'user' || m.role === 'assistant') && m.content)
        .slice(-10)
        .map(m => ({ role: m.role, content: m.content }));
      agentApi.companionChat(question, history).then((data) => {
        const answer = (data && data.answer) || '我这边有点没听清，您再说一遍好吗？';
        this.setData({
          chatHistory: [...this.data.chatHistory, { role: 'assistant', content: answer, canPlay: true }],
          isLoading: false
        });
        this._saveHistory();
        // 陪伴助手：不自动播报，点小喇叭才按需播放
      }).catch((err) => {
        console.error('陪伴助手请求失败:', err);
        this.setData({
          chatHistory: [...this.data.chatHistory, {
            role: 'assistant', content: '暂时连不上服务，您稍后再和我聊好吗？'
          }],
          isLoading: false
        });
        this._saveHistory();
      });
      return;
    }

    // 健康助手：调用真实代码层智能体
    agentApi.healthChat({
      question,
      sessionId: this.data.sessionId
    }).then((data) => {
      this.setData({ sessionId: data.session_id || this.data.sessionId });
      const msg = {
        role: 'assistant',
        content: data.answer,
        emergency: !!data.is_emergency,
        toolCount: (data.tool_traces || []).length,
        refs: (data.rag_refs || []).map(r => r.title)
      };
      this.setData({
        chatHistory: [...this.data.chatHistory, msg],
        isLoading: false
      });
      if (data.is_emergency) {
        wx.vibrateShort && wx.vibrateShort({ type: 'medium' });
      }
      // 控制台留痕，便于演示时看到“查了哪些数据/引用了哪些知识”
      console.log('工具调用:', data.tool_traces);
      console.log('知识引用:', data.rag_refs);
      // 方言朗读
      if (this.data.autoSpeak) this.speak(data.answer);
    }).catch((err) => {
      console.error('健康助手请求失败:', err);
      this.setData({
        chatHistory: [...this.data.chatHistory, {
          role: 'assistant',
          content: '暂时连不上健康服务，请确认后端已启动后再试。'
        }],
        isLoading: false
      });
    });
  },

  // 文字 -> 方言语音并播放
  speak(text, idx) {
    if (!text) return;
    agentApi.synthesize(text, this.data.selectedDialect).then((url) => {
      if (!this._audio || !url) return;
      if (idx != null) this.setData({ [`chatHistory[${idx}].audioUrl`]: url });
      this._audio.src = url;
      this._audio.play();
    }).catch((err) => console.warn('语音合成失败:', err));
  },

  // 点某条回复的小喇叭：播放/暂停/继续切换
  playReply(e) {
    const idx = e.currentTarget.dataset.idx;
    const msg = this.data.chatHistory[idx];
    if (!msg || !msg.content) return;
    // 正在播这条 → 暂停
    if (this._playingIdx === idx && !this._paused) {
      this._audio.pause();
      this._paused = true;
      return;
    }
    // 这条已暂停 → 继续
    if (this._playingIdx === idx && this._paused) {
      this._audio.play();
      this._paused = false;
      return;
    }
    // 新播这条
    this._playingIdx = idx;
    this._paused = false;
    if (msg.audioUrl) {
      this._audio.stop();
      this._audio.src = msg.audioUrl;
      this._audio.play();
      return;
    }
    this.speak(msg.content, idx);
  },

  startVoiceRecording() {
    if (this.data.isRecording) {
      this.data.recordManager.stop();
      this.setData({ isRecording: false });
    } else {
      this.data.recordManager.start({
        duration: 60000,
        sampleRate: 16000,
        numberOfChannels: 1,
        encodeBitRate: 48000,
        format: 'wav'   // wav 带标准头、16k单声道，对语音识别最稳
      });
      this.setData({ isRecording: true });
      wx.showToast({ title: '正在录音...', icon: 'none' });
    }
  },

  // 录音 -> 后端 ASR 转文字 -> 自动发问
  uploadVoice(tempFilePath, meta) {
    const size = meta && meta.size;
    const duration = meta && meta.duration;
    console.log('待上传录音:', tempFilePath, '大小:', size, '时长ms:', duration);
    // 录音太短或文件过小，直接提示，不浪费请求
    if ((size !== undefined && size < 1200) || (duration !== undefined && duration < 400)) {
      wx.showToast({ title: '录音太短，请按住多说几秒', icon: 'none' });
      return;
    }
    wx.showLoading({ title: '正在识别...', mask: true });
    agentApi.recognizeVoice(tempFilePath, this.data.selectedDialect, 'wav')
      .then((data) => {
        wx.hideLoading();
        const text = (data && data.text || '').trim();
        if (!text) {
          wx.showToast({ title: '没听清，请靠近手机再说一次', icon: 'none' });
          return;
        }
        this.askBackend(text);
      })
      .catch((err) => {
        wx.hideLoading();
        console.error('语音识别失败:', err);
        wx.showToast({ title: '识别失败，可改用文字输入', icon: 'none' });
      });
  },

  changeDialect(e) {
    const selectedIndex = e.detail.value;
    const dialect = this.data.dialects[selectedIndex];
    this.setData({
      selectedDialectIndex: selectedIndex,
      selectedDialect: dialect ? dialect.value : 'mandarin',
      selectedDialectLabel: dialect ? dialect.label : '普通话'
    });
  },

  clearChat() {
    wx.showModal({
      title: '清空对话',
      content: '确定要清空当前聊天记录吗？',
      confirmText: '清空',
      success: (res) => {
        if (res.confirm) {
          if (this._audio) { this._audio.stop(); this._playingIdx = -1; this._paused = false; }
          if (this._cacheKey) { try { wx.removeStorageSync(this._cacheKey); } catch (e) {} }
          this.setData({ chatHistory: [{ role: 'assistant', content: this._welcome || '' }] });
          this.showToast && wx.showToast({ title: '已清空', icon: 'none' });
        }
      }
    });
  }
});
