Page({
  data: {
    healthData: {
      bloodPressure: '120/80',
      heartRate: '65',
      bloodSugar: '7.2'
    },
    // 本周血压趋势（柱高 rpx，收缩压）
    bpTrend: [
      { day: '一', height: 90,  high: false },
      { day: '二', height: 110, high: true  },
      { day: '三', height: 100, high: false },
      { day: '四', height: 120, high: true  },
      { day: '五', height: 115, high: true  },
      { day: '六', height: 85,  high: false },
      { day: '日', height: 95,  high: false }
    ],
    reminders: [
      {
        id: 1,
        title: '服用降压药',
        time: '今天 08:00',
        type: 'medicine',
        status: 'done'
      },
      {
        id: 2,
        title: '喝水提醒',
        time: '今天 10:00',
        type: 'water',
        status: 'pending'
      }
    ],
    websocketUrl: 'ws://localhost:8000/ws/reminders',
    websocketTask: null
  },

  onLoad() {
    console.log('健康模块主页面加载');
    this.loadHealthData();
    this.loadReminders();
    this.connectWebSocket();
  },

  onShow() {
    console.log('健康模块主页面显示');
    if (typeof this.getTabBar === 'function' && this.getTabBar()) {
      this.getTabBar().setData({ selected: 1 });
    }
    if (!this.data.websocketTask) {
      this.connectWebSocket();
    }
  },

  onHide() {
    if (this.data.websocketTask) {
      this.data.websocketTask.close();
      this.setData({ websocketTask: null });
    }
  },

  onUnload() {
    if (this.data.websocketTask) {
      this.data.websocketTask.close();
      this.setData({ websocketTask: null });
    }
  },

  loadHealthData() {
    setTimeout(() => {
      console.log('健康数据加载完成');
    }, 1000);
  },

  loadReminders() {
    setTimeout(() => {
      console.log('提醒数据加载完成');
    }, 1000);
  },

  readMore() {
    wx.showToast({
      title: '健康知识详情',
      icon: 'none'
    });
  },

  goToMedicine() {
    wx.navigateTo({ url: '/pages/health/medicine/medicine' });
  },

  /**
   * 连接WebSocket
   */
  connectWebSocket() {
    const that = this;
    const websocketTask = wx.connectSocket({
      url: that.data.websocketUrl,
      success: function(res) {
        console.log('WebSocket连接成功');
        that.setData({ websocketTask: websocketTask });
      },
      fail: function(err) {
        console.error('WebSocket连接失败:', err);
      }
    });

    // 监听WebSocket连接打开
    websocketTask.onOpen(function(res) {
      console.log('WebSocket连接已打开');
    });

    // 监听WebSocket接收消息
    websocketTask.onMessage(function(res) {
      console.log('收到WebSocket消息:', res.data);
      const reminder = JSON.parse(res.data);
      
      // 添加提醒到列表
      const newReminder = {
        id: Date.now(),
        title: reminder.message,
        time: '今天 ' + reminder.time,
        type: reminder.type,
        status: 'pending'
      };
      
      that.setData({
        reminders: [newReminder, ...that.data.reminders]
      });

      // 显示提醒弹窗
      wx.showModal({
        title: '提醒',
        content: reminder.message,
        showCancel: false,
        confirmText: '知道了'
      });
    });

    // 监听WebSocket错误
    websocketTask.onError(function(err) {
      console.error('WebSocket错误:', err);
    });

    // 监听WebSocket关闭
    websocketTask.onClose(function(res) {
      console.log('WebSocket连接已关闭');
      that.setData({ websocketTask: null });
    });
  }
});