// monitor.js —— 实时监护：WebSocket 接收后端 detector 推来的 JPEG 帧（约15fps）+ 跌倒状态
const { BASE_URL } = require('../../utils/config')
const alertApi = require('../../services/alert-api.js')
// 从主后端地址推导 detector 推流地址（同主机，端口 5002）
const _hostMatch = BASE_URL.match(/^https?:\/\/([^:/]+)/)
const STREAM_HOST = _hostMatch ? _hostMatch[1] : 'localhost'
const WS_URL = `ws://${STREAM_HOST}:5002/ws/stream`

Page({
  data: {
    currentTime: '',
    monitorStatus: '连接中…',
    roomStatus: '有人',
    activity: '活动',
    monitorFrame: '',
    isMonitorOn: true,
    fps: 0,
    fallRecords: [],
    showRecords: false,   // 仅子女端显示跌倒记录；老人端只看实时画面
    history: [
      { time: '10:30', event: '正常活动', desc: '老人在客厅活动' },
      { time: '08:15', event: '正常活动', desc: '老人起床' },
      { time: '22:00', event: '正常活动', desc: '老人入睡' }
    ]
  },

  onLoad() {
    this.updateCurrentTime()
    // 仅子女端显示跌倒记录；老人端/社区端只看画面
    const role = wx.getStorageSync('role') || 'parent'
    this.setData({ showRecords: role === 'daughter' })
    this.timer = setInterval(() => {
      this.updateCurrentTime()
    }, 60000)
    // 错峰：等上一页(子女首页)的提醒 socket 完成关闭再连推流，避免全局单 socket 抢占
    setTimeout(() => this.connectStream(), 300)
  },

  onShow() {
    if (this.data.showRecords) this.loadFallRecords()
  },

  onUnload() {
    if (this.timer) clearInterval(this.timer)
    this.closeStream()
  },

  // 拉取历史跌倒记录（含现场截图）
  loadFallRecords() {
    alertApi.listFallRecords().then((list) => {
      this.setData({ fallRecords: list })
    })
  },

  // 点击缩略图看大图
  previewRecord(e) {
    const url = e.currentTarget.dataset.url
    if (!url) return
    const urls = this.data.fallRecords.map(r => r.snapshotUrl).filter(Boolean)
    wx.previewImage({ current: url, urls: urls.length ? urls : [url] })
  },

  updateCurrentTime() {
    const now = new Date()
    const p = (n) => String(n).padStart(2, '0')
    this.setData({
      currentTime: `${now.getFullYear()}-${p(now.getMonth() + 1)}-${p(now.getDate())} ${p(now.getHours())}:${p(now.getMinutes())}`
    })
  },

  // 建立 WebSocket 监控流
  connectStream() {
    if (!this.data.isMonitorOn) return
    this._fallNotified = false
    this._socketOpen = false
    wx.connectSocket({ url: WS_URL })

    wx.onSocketOpen(() => {
      this._socketOpen = true
      this.setData({ monitorStatus: '正常' })
    })

    wx.onSocketMessage((res) => {
      // 文本帧 = 状态；二进制帧 = JPEG 画面
      if (typeof res.data === 'string') {
        let st
        try { st = JSON.parse(res.data) } catch (e) { return }
        if (st.type !== 'status') return
        this.setData({ fps: st.fps })
        if (st.fall) {
          this.setData({ monitorStatus: '跌倒告警', activity: '疑似跌倒' })
          if (!this._fallNotified) {
            this._fallNotified = true
            wx.vibrateShort && wx.vibrateShort({ type: 'heavy' })
            wx.showToast({ title: '检测到跌倒，已通知家属', icon: 'none' })
          }
        } else {
          this._fallNotified = false
          this.setData({ monitorStatus: '正常', activity: '活动' })
        }
      } else {
        const b64 = wx.arrayBufferToBase64(res.data)
        this.setData({ monitorFrame: 'data:image/jpeg;base64,' + b64 })
      }
    })

    wx.onSocketError(() => {
      this.setData({ monitorStatus: '监控未连接' })
    })
    wx.onSocketClose(() => {
      if (this.data.isMonitorOn) this.setData({ monitorStatus: '监控已断开' })
    })
  },

  closeStream() {
    try { wx.closeSocket({}) } catch (e) {}
  },

  // 切换监控开关
  toggleMonitor(e) {
    const isMonitorOn = e.detail.value
    this.setData({ isMonitorOn })
    if (isMonitorOn) {
      this.connectStream()
    } else {
      this.closeStream()
      this.setData({ monitorFrame: '', monitorStatus: '已关闭', activity: '无', fps: 0 })
    }
  },

  viewMonitorDetail() {
    wx.showModal({
      title: '监控详情',
      content: `当前状态: ${this.data.monitorStatus}\n活动状态: ${this.data.activity}\n帧率: ${this.data.fps}fps\n时间: ${this.data.currentTime}\n监控: ${this.data.isMonitorOn ? '开启' : '关闭'}`,
      showCancel: false
    })
  }
})
