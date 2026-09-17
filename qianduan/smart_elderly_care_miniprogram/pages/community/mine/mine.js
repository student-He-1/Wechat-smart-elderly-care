// community/mine.js
Page({
  goHome() { wx.reLaunch({ url: '/pages/community/home/home' }); },
  goAlert() { wx.reLaunch({ url: '/pages/community/alert/alert' }); },
  goElders() { wx.reLaunch({ url: '/pages/community/elders/elders' }); },
  goMine() { wx.reLaunch({ url: '/pages/community/mine/mine' }); },

  goProfile() {
    wx.navigateTo({ url: '/pages/community/profile/profile' });
  },

  switchRole() {
    wx.showActionSheet({
      itemList: ['切回老人端', '切回子女端'],
      success: (res) => {
        if (res.tapIndex === 0) {
          wx.setStorageSync('role', 'parent');
          wx.reLaunch({ url: '/pages/index/index' });
        } else {
          wx.setStorageSync('role', 'daughter');
          wx.reLaunch({ url: '/pages/daughter/home/home' });
        }
      }
    });
  },

  resetData() {
    wx.showModal({
      title: '重置演示数据',
      content: '将清空告警和工单状态，确定？',
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
      content: '智慧养老社区端 · v1.0.0\n演示项目，所有数据均为模拟。',
      showCancel: false
    });
  }
});
