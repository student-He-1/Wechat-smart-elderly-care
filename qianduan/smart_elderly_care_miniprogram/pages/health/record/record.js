// record.js
const request = require('../../../utils/request.js')

Page({
  data: {
    records: [],
    showModal: false,
    formData: {
      content: ''
    },
    inputMethod: 'text', // 'text' or 'voice'
    isRecording: false
  },

  onLoad() {
    // 页面加载时获取健康记录列表
    this.loadRecords()
  },

  onShow() {
    // 页面显示时刷新记录列表
    this.loadRecords()
  },

  // 加载健康记录列表
  loadRecords() {
    request.get('/health/record').then(res => {
      if (res.message === '获取健康记录列表成功') {
        // 格式化时间
        const formattedRecords = res.data.map(record => ({
          ...record,
          created_at: this.formatTime(record.created_at)
        }))
        this.setData({
          records: formattedRecords
        })
      }
    }).catch(err => {
      console.error('获取健康记录失败:', err)
    })
  },

  // 格式化时间
  formatTime(timeString) {
    const date = new Date(timeString)
    return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
  },

  // 显示添加记录弹窗
  showAddRecordModal() {
    this.setData({
      showModal: true,
      formData: {
        content: ''
      },
      inputMethod: 'text',
      isRecording: false
    })
  },

  // 隐藏弹窗
  hideModal() {
    this.setData({
      showModal: false
    })
  },

  // 输入框绑定
  bindInput(e) {
    const field = e.currentTarget.dataset.field
    const value = e.detail.value
    this.setData({
      [`formData.${field}`]: value
    })
  },

  // 切换输入方式
  switchInputMethod() {
    this.setData({
      inputMethod: this.data.inputMethod === 'text' ? 'voice' : 'text'
    })
  },

  // 开始录音
  startVoiceRecording() {
    if (this.data.isRecording) {
      // 停止录音
      wx.stopRecord()
      this.setData({
        isRecording: false
      })
      wx.showToast({
        title: '录音结束',
        icon: 'success'
      })
      // 模拟语音识别结果
      setTimeout(() => {
        this.setData({
          'formData.content': '今天感觉有点头晕，可能是血压有点高'
        })
      }, 1000)
    } else {
      // 开始录音
      wx.startRecord({
        success: (res) => {
          const tempFilePath = res.tempFilePath
          console.log('录音成功:', tempFilePath)
          // 这里可以调用语音识别API
        },
        fail: (err) => {
          console.error('录音失败:', err)
          wx.showToast({
            title: '录音失败，请重试',
            icon: 'none'
          })
        }
      })
      this.setData({
        isRecording: true
      })
      wx.showToast({
        title: '正在录音...',
        icon: 'none'
      })
    }
  },

  // 提交表单
  submitForm() {
    const content = this.data.formData.content.trim()
    
    // 表单验证
    if (!content) {
      wx.showToast({
        title: '请输入记录内容',
        icon: 'none'
      })
      return
    }

    // 添加健康记录
    request.post('/health/record', this.data.formData).then(res => {
      if (res.message === '健康记录添加成功') {
        wx.showToast({
          title: '记录添加成功',
          icon: 'success'
        })
        this.hideModal()
        this.loadRecords()
      }
    }).catch(err => {
      console.error('添加健康记录失败:', err)
      wx.showToast({
        title: '添加失败，请重试',
        icon: 'none'
      })
    })
  }
});
