// assistant.js —— 健康小助手（唯一健康助手页：真后端 Agent + 语音输入 + 手动播报 + 对话持久化）
const agentApi = require('../../../services/agent-api')
const { currentIdentity } = require('../../../utils/config')

Page({
  data: {
    inputValue: '',
    chatHistory: [],
    isLoading: false,
    isRecording: false,
    recordManager: null,
    sessionId: null,
    userAvatar: '/assets/images/6-3.png',
    scrollTop: 0,
    commonQuestions: [
      '高血压怎么办？',
      '糖尿病如何饮食？',
      '如何改善失眠？',
      '老年人如何锻炼？',
      '便秘怎么办？',
      '如何预防感冒？',
      '血糖高要注意什么？',
      '降压药能随便停吗？',
      '老人头晕要注意啥？'
    ],
    commonRow1: [
      '高血压怎么办？',
      '糖尿病如何饮食？',
      '如何改善失眠？',
      '老年人如何锻炼？',
      '便秘怎么办？'
    ],
    commonRow2: [
      '如何预防感冒？',
      '血糖高要注意什么？',
      '降压药能随便停吗？',
      '老人头晕要注意啥？'
    ],
    dialects: [
      { value: 'mandarin', label: '普通话' },
      { value: 'sichuan', label: '四川话' },
      { value: 'northeast', label: '东北话' }
    ],
    selectedDialectIndex: 0,
    selectedDialect: 'mandarin',
    selectedDialectLabel: '普通话'
  },

  onLoad() {
    this._audio = wx.createInnerAudioContext()
    this._playingIndex = -1
    this._paused = false
    this._audio.onEnded(() => { this._playingIndex = -1; this._paused = false })
    this._audio.onStop(() => { this._playingIndex = -1; this._paused = false })
    this._audio.onError((err) => {
      console.error('语音播放错误:', err)
      wx.showToast({ title: '语音播放失败，请检查网络', icon: 'none' })
    })
    // 当前身份（老人 elder / 子女 daughter），决定 Agent 视角与缓存隔离
    const identity = currentIdentity()
    this.askerRole = identity.backendRole
    this.cacheKey = 'health_chat_' + identity.backendRole
    this.setData({ userAvatar: identity.backendRole === 'daughter' ? '/assets/images/6-2.png' : '/assets/images/6-3.png' })
    this.initRecordManager()
    this.restoreHistory()
  },

  onUnload() {
    if (this._audio) {
      this._audio.destroy()
      this._audio = null
    }
  },

  // 恢复上次对话（翻出去再回来不丢失）
  restoreHistory() {
    const cache = wx.getStorageSync(this.cacheKey)
    if (cache && Array.isArray(cache.chatHistory) && cache.chatHistory.length) {
      const history = cache.chatHistory.map((m) => m.segments
        ? m
        : Object.assign({}, m, { segments: [{ type: 'text', text: m.content || '' }] }))
      this.setData({
        chatHistory: history,
        sessionId: cache.sessionId || null
      })
    } else {
      this.addSystemMessage('您好，我是您的健康小助手，有什么健康问题可以问我哦！')
    }
  },

  persist() {
    // 临时音频路径不持久化（退出后失效）
    const saved = this.data.chatHistory.map((m) => {
      const copy = Object.assign({}, m)
      delete copy.audioPath
      return copy
    })
    wx.setStorageSync(this.cacheKey, {
      sessionId: this.data.sessionId,
      chatHistory: saved,
      ts: Date.now()
    })
  },

  // 清空对话并重新开始
  clearChat() {
    wx.showModal({
      title: '清空对话',
      content: '确定清空当前对话、重新开始吗？',
      confirmText: '清空',
      cancelText: '取消',
      success: (res) => {
        if (!res.confirm) return
        if (this._audio) { this._audio.stop(); this._playingIndex = -1; this._paused = false }
        wx.removeStorageSync(this.cacheKey)
        this.setData({ chatHistory: [], sessionId: null, inputValue: '' })
        this.addSystemMessage('您好，我是您的健康小助手，有什么健康问题可以问我哦！')
      }
    })
  },

  addSystemMessage(content) {
    this.setData({
      chatHistory: [...this.data.chatHistory, {
        role: 'assistant', content, segments: [{ type: 'text', text: content }]
      }]
    })
  },

  // 把含 {{术语}} 的回答拆成片段：text 普通文字 / term 可点术语
  _splitTerms(text) {
    const segs = []
    const re = /{{\s*([^}]+?)\s*}}/g
    let last = 0
    let m
    while ((m = re.exec(text))) {
      if (m.index > last) segs.push({ type: 'text', text: text.slice(last, m.index) })
      segs.push({ type: 'term', text: m[1].trim() })
      last = m.index + m[0].length
    }
    if (last < text.length) segs.push({ type: 'text', text: text.slice(last) })
    return segs.length ? segs : [{ type: 'text', text }]
  },

  // 后台预生成术语解释，结果挂到该条消息；同时把 Promise 挂起，解释页可复用、不重复请求
  prefetchBranch(msgIndex, term) {
    const parentSessionId = this.data.sessionId
    if (!parentSessionId) return
    const p = agentApi.openBranch({ parentSessionId, term, askerRole: this.askerRole })
      .then((bd) => {
        this.setData({
          [`chatHistory[${msgIndex}].branchSessionId`]: bd.session_id,
          [`chatHistory[${msgIndex}].branchAnswer`]: bd.answer
        })
        return bd
      })
      .catch(() => null)
    this._branchPromises = this._branchPromises || {}
    this._branchPromises[msgIndex] = p
  },

  // 展开/收起思考过程
  // 流式时把页面自动拉到底，让对话框始终跟在最新内容下方
  _scrollBottom() {
    this._tick = (this._tick || 0) + 1
    this.setData({ scrollTop: 999999 + this._tick })
  },

  toggleThink(e) {
    const i = e.currentTarget.dataset.index
    this.setData({ [`chatHistory[${i}].thinkingOpen`]: !this.data.chatHistory[i].thinkingOpen })
  },

  // 点术语：把预取结果/进行中的 Promise 带到全局，解释页优先复用
  openBranch(e) {
    const term = e.currentTarget.dataset.term
    const index = e.currentTarget.dataset.index
    if (!term) return
    const msg = this.data.chatHistory[index] || {}
    const g = getApp()
    g.globalData = g.globalData || {}
    g.globalData.pendingBranch = {
      term,
      answer: msg.branchAnswer || '',
      sessionId: msg.branchSessionId || null,
      promise: (this._branchPromises || {})[index] || null
    }
    wx.navigateTo({
      url: `/pages/health/explain/explain?term=${encodeURIComponent(term)}&sessionId=${this.data.sessionId || ''}&depth=1`
    })
  },

  bindInput(e) {
    this.setData({ inputValue: e.detail.value })
  },

  changeDialect(e) {
    const selectedIndex = e.detail.value
    const dialect = this.data.dialects[selectedIndex]
    // 切换方言后，之前预合成的音频失效，清掉缓存
    const resetAudio = this.data.chatHistory.map((m) => {
      const copy = Object.assign({}, m)
      copy.audioPath = ''
      return copy
    })
    this.setData({
      selectedDialectIndex: selectedIndex,
      selectedDialect: dialect ? dialect.value : 'mandarin',
      selectedDialectLabel: dialect ? dialect.label : '普通话',
      chatHistory: resetAudio
    })
  },

  // 文字发送
  sendQuestion() {
    const question = this.data.inputValue.trim()
    if (!question) {
      wx.showToast({ title: '请输入问题', icon: 'none' })
      return
    }
    this.setData({ inputValue: '' })
    this.askAgent(question)
  },

  // 点常见问题直接发问
  selectQuestion(e) {
    const question = e.currentTarget.dataset.question
    this.askAgent(question)
  },

  // 统一走真后端健康智能体
  askAgent(question) {
    // 先放入用户消息 + 一条占位 AI 消息，流式往里逐字填
    this.setData({
      chatHistory: [...this.data.chatHistory,
        { role: 'user', content: question },
        { role: 'assistant', content: '', segments: [{ type: 'text', text: '' }], thinking: '', thinkingOpen: true }
      ],
      isLoading: true
    })
    const aiIndex = this.data.chatHistory.length - 1
    let full = ''
    let thinkingBuf = ''
    // 思考流高频，节流到每 200ms 刷一次，避免逐字 setData 卡死
    const flushThinking = () => {
      if (thinkingBuf) {
        this.setData({ [`chatHistory[${aiIndex}].thinking`]: thinkingBuf })
      }
    }
    const thinkTimer = setInterval(flushThinking, 200)

    agentApi.healthChatStream({
      question,
      sessionId: this.data.sessionId,
      askerRole: this.askerRole,
      onReasoning: (t) => {
        thinkingBuf += t
        this.setData({ isLoading: false })
        this._scrollBottom()
      },
      onDelta: (text) => {
        full += text
        this.setData({
          isLoading: false,
          [`chatHistory[${aiIndex}].content`]: full,
          [`chatHistory[${aiIndex}].segments[0].text`]: full
        })
        this._scrollBottom()
      },
      onEnd: (meta) => {
        clearInterval(thinkTimer)
        flushThinking()
        this.setData({ sessionId: meta.session_id || this.data.sessionId })
        // 以后端清洗后的最终文本为准（已剔除不该标的术语）
        const finalText = meta.answer || full || ''
        const clean = finalText.replace(/{{\s*([^}]+?)\s*}}/g, '$1')
        const segments = (this.askerRole === 'daughter')
          ? this._splitTerms(finalText)
          : [{ type: 'text', text: clean }]
        this.setData({
          [`chatHistory[${aiIndex}].content`]: clean,
          [`chatHistory[${aiIndex}].segments`]: segments,
          [`chatHistory[${aiIndex}].emergency`]: !!meta.is_emergency,
          isLoading: false
        })
        this._scrollBottom()
        this.persist()
        this.prefetchSpeak(aiIndex, clean)
        // 不再后台预生成术语解释：主线回答完就结束，点开术语时现场流式（1秒出字），避免抢资源
        if (meta.is_emergency) {
          wx.vibrateShort && wx.vibrateShort({ type: 'medium' })
          wx.showToast({ title: '检测到紧急情况，请及时就医', icon: 'none' })
        }
      },
      onError: (err) => {
        console.error('健康问答失败:', err)
        clearInterval(thinkTimer)
        this.setData({
          [`chatHistory[${aiIndex}].content`]: '暂时连不上健康服务，请确认后端已启动后再试。',
          [`chatHistory[${aiIndex}].segments`]: [{ type: 'text', text: '暂时连不上健康服务，请确认后端已启动后再试。' }],
          isLoading: false
        })
        this.persist()
      }
    })
  },

  // ===== 语音输入 =====
  initRecordManager() {
    const rm = wx.getRecorderManager()
    this.setData({ recordManager: rm })
    rm.onStart(() => {})
    rm.onStop((res) => {
      this.uploadVoice(res.tempFilePath, { size: res.fileSize, duration: res.duration })
    })
    rm.onError(() => {
      this.setData({ isRecording: false })
      wx.showToast({ title: '录音失败，请重试', icon: 'none' })
    })
  },

  startVoiceRecording() {
    const rm = this.data.recordManager
    if (!rm) return
    if (this.data.isRecording) {
      rm.stop()
      this.setData({ isRecording: false })
    } else {
      rm.start({
        duration: 60000,
        sampleRate: 16000,
        numberOfChannels: 1,
        encodeBitRate: 48000,
        format: 'wav'
      })
      this.setData({ isRecording: true })
      wx.showToast({ title: '正在录音，再点结束', icon: 'none' })
    }
  },

  // 录音 -> ASR 转文字 -> 自动发问
  uploadVoice(tempFilePath, meta) {
    const size = meta && meta.size
    const duration = meta && meta.duration
    if ((size !== undefined && size < 1200) || (duration !== undefined && duration < 400)) {
      wx.showToast({ title: '录音太短，请按住多说几秒', icon: 'none' })
      return
    }
    wx.showLoading({ title: '正在识别...', mask: true })
    agentApi.recognizeVoice(tempFilePath, this.data.selectedDialect, 'wav')
      .then((data) => {
        wx.hideLoading()
        const text = (data && data.text || '').trim()
        if (!text) {
          wx.showToast({ title: '没听清，请靠近手机再说一次', icon: 'none' })
          return
        }
        this.askAgent(text)
      })
      .catch((err) => {
        wx.hideLoading()
        console.error('语音识别失败:', err)
        wx.showToast({ title: '识别失败，可改用文字输入', icon: 'none' })
      })
  },

  // 后台预合成：文字 -> TTS url -> 下载本地，缓存到该条消息，点播报时零等待
  prefetchSpeak(index, text) {
    this._buildAudio(text)
      .then((path) => this._cacheAudio(index, path))
      .catch((err) => console.warn('语音预取失败（不影响使用）:', err))
  },

  _buildAudio(text) {
    return agentApi.synthesize(text, this.data.selectedDialect)
      .then((url) => new Promise((resolve, reject) => {
        wx.downloadFile({
          url,
          success: (r) => (r.statusCode === 200 ? resolve(r.tempFilePath) : reject(new Error('download fail'))),
          fail: reject
        })
      }))
  },

  _cacheAudio(index, path) {
    this.setData({ [`chatHistory[${index}].audioPath`]: path })
  },

  _play(path) {
    if (!this._audio) this._audio = wx.createInnerAudioContext()
    this._audio.stop()
    this._audio.src = path
    this._audio.play()
  },

  // 手动语音播报：点哪条播哪条；再点暂停，再点继续
  speakAnswer(e) {
    const index = e.currentTarget.dataset.index
    const msg = this.data.chatHistory[index]
    if (!msg || !msg.content) return

    // 正在播这条 → 暂停
    if (this._playingIndex === index && !this._paused) {
      this._audio.pause()
      this._paused = true
      return
    }
    // 这条已暂停 → 继续
    if (this._playingIndex === index && this._paused) {
      this._audio.play()
      this._paused = false
      return
    }
    // 新播一条
    this._playingIndex = index
    this._paused = false
    if (msg.audioPath) {
      this._play(msg.audioPath)
      return
    }
    wx.showLoading({ title: '准备播报...', mask: true })
    this._buildAudio(msg.content)
      .then((path) => {
        wx.hideLoading()
        this._cacheAudio(index, path)
        this._play(path)
      })
      .catch((err) => {
        wx.hideLoading()
        console.error('语音播报失败:', err)
        wx.showToast({ title: '语音服务暂时不可用', icon: 'none' })
      })
  }
})
