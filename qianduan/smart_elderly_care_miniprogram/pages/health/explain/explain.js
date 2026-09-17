// explain.js —— 术语解释子对话（流式逐字；第一层可再解释一个术语，第二层即止）
const agentApi = require('../../../services/agent-api')
const { currentIdentity } = require('../../../utils/config')

Page({
  data: {
    term: '',
    sessionId: null,
    chatHistory: [],
    inputValue: '',
    isLoading: false,
    scrollTop: 0
  },

  onLoad(options) {
    const term = decodeURIComponent(options.term || '')
    this.parentSessionId = options.sessionId ? Number(options.sessionId) : null
    this.depth = Number(options.depth || 1)
    this.askerRole = (currentIdentity() || {}).backendRole || 'daughter'
    this.setData({
      term,
      chatHistory: [{ role: 'system', content: `正在为您解释「${term}」，内容独立于主线对话。` }]
    })

    const g = getApp()
    const pending = (g.globalData && g.globalData.pendingBranch) || null
    if (pending && pending.term === term) {
      g.globalData.pendingBranch = null
      if (pending.answer) {
        this.setData({
          sessionId: pending.sessionId || this.parentSessionId,
          chatHistory: [
            { role: 'system', content: `正在为您解释「${term}」，内容独立于主线对话。` },
            { role: 'assistant', content: pending.answer }
          ]
        })
        return
      }
      // 预加载还没好：不挡屏干等，直接现场流式逐字出
      g.globalData.pendingBranch = null
    }

    // 兜底：流式现场生成
    this._streamIn({ question: '', sessionId: this.parentSessionId, branchTerm: term, hideLoading: true })
  },

  backToMain() { wx.navigateBack() },

  bindInput(e) { this.setData({ inputValue: e.detail.value }) },

  _appendPlain(text) {
    this.setData({ chatHistory: [...this.data.chatHistory, { role: 'assistant', content: text }] })
  },

  // 追加一条占位 AI 消息，返回其索引
  _pushAiPlaceholder() {
    this.setData({
      chatHistory: [...this.data.chatHistory,
        { role: 'assistant', content: '', segments: [{ type: 'text', text: '' }] }],
      isLoading: true
    })
    return this.data.chatHistory.length - 1
  },

  _scrollBottom() {
    this._tick = (this._tick || 0) + 1
    this.setData({ scrollTop: 999999 + this._tick })
  },

  // 流式写入指定索引的消息
  toggleThink(e) {
    const i = e.currentTarget.dataset.index
    this.setData({ [`chatHistory[${i}].thinkingOpen`]: !this.data.chatHistory[i].thinkingOpen })
  },

  _streamIn({ question, sessionId, branchTerm }) {
    const aiIndex = this._pushAiPlaceholder()
    let full = ''
    let thinkingBuf = ''
    const flushThinking = () => {
      if (thinkingBuf) this.setData({ [`chatHistory[${aiIndex}].thinking`]: thinkingBuf })
    }
    const thinkTimer = setInterval(flushThinking, 200)
    agentApi.healthChatStream({
      question, sessionId, branchTerm, askerRole: this.askerRole,
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
        if (meta.session_id) this.setData({ sessionId: meta.session_id })
        this._scrollBottom()
        const finalText = meta.answer || full || ''
        const clean = finalText.replace(/{{\s*([^}]+?)\s*}}/g, '$1')
        const segs = (this.depth === 1)
          ? this._splitTerms(finalText)
          : [{ type: 'text', text: clean }]
        this.setData({
          [`chatHistory[${aiIndex}].content`]: clean,
          [`chatHistory[${aiIndex}].segments`]: segs,
          isLoading: false
        })
      },
      onError: () => {
        clearInterval(thinkTimer)
        this.setData({
          [`chatHistory[${aiIndex}].content`]: '连接失败，请稍后再试。',
          isLoading: false
        })
      }
    })
  },

  _splitTerms(text) {
    const segs = []
    const re = /{{\s*([^}]+?)\s*}}/g
    let last = 0, m
    while ((m = re.exec(text))) {
      if (m.index > last) segs.push({ type: 'text', text: text.slice(last, m.index) })
      segs.push({ type: 'term', text: m[1].trim() })
      last = m.index + m[0].length
    }
    if (last < text.length) segs.push({ type: 'text', text: text.slice(last) })
    return segs.length ? segs : [{ type: 'text', text }]
  },

  openSubBranch(e) {
    const term = e.currentTarget.dataset.term
    if (!term) return
    wx.navigateTo({
      url: `/pages/health/explain/explain?term=${encodeURIComponent(term)}&sessionId=${this.data.sessionId || ''}&depth=${this.depth + 1}`
    })
  },

  sendQuestion() {
    const question = this.data.inputValue.trim()
    if (!question) return
    this.setData({ inputValue: '', chatHistory: [...this.data.chatHistory, { role: 'user', content: question }] })
    this._streamIn({ question, sessionId: this.data.sessionId })
  }
})
