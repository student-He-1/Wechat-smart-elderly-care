// daughter/mine.js
Page({
  data: { tab: 'mine' },

  goHome() { wx.reLaunch({ url: '/pages/daughter/home/home' }); },
  goAlerts() { wx.reLaunch({ url: '/pages/daughter/alerts/alerts' }); },
  goServices() { wx.reLaunch({ url: '/pages/daughter/services/services' }); },
  goMine() { wx.reLaunch({ url: '/pages/daughter/mine/mine' }); },

  goProfile() {
    wx.navigateTo({ url: '/pages/daughter/profile/profile' });
  },

  switchRole() {
    wx.showActionSheet({
      itemList: ['切换到老人端', '切换到社区端'],
      success: (res) => {
        if (res.tapIndex === 0) {
          wx.setStorageSync('role', 'parent');
          wx.reLaunch({ url: '/pages/index/index' });
        } else if (res.tapIndex === 1) {
          wx.setStorageSync('role', 'community');
          wx.reLaunch({ url: '/pages/community/home/home' });
        }
      }
    });
  },

  resetData() {
    wx.showModal({
      title: '重置演示数据',
      content: '将清空所有告警和模拟数据，确定？',
      success: (res) => {
        if (res.confirm) {
          wx.removeStorageSync('alerts');
          wx.showToast({ title: '已重置', icon: 'success' });
        }
      }
    });
  },

  showAbout() {
    wx.showModal({
      title: '关于',
      content: '智慧养老子女端 · v1.0.0\n演示项目，所有数据均为模拟。',
      showCancel: false
    });
  }
});
