// splash.js —— 启动页：判断身份并跳转
Page({
  onLoad() {
    const role = wx.getStorageSync('role');
    if (role === 'parent') {
      wx.reLaunch({ url: '/pages/index/index' });
    } else if (role === 'daughter') {
      wx.reLaunch({ url: '/pages/daughter/home/home' });
    } else if (role === 'community') {
      wx.reLaunch({ url: '/pages/community/home/home' });
    }
  },

  chooseParent() {
    wx.setStorageSync('role', 'parent');
    wx.reLaunch({ url: '/pages/index/index' });
  },

  chooseDaughter() {
    wx.setStorageSync('role', 'daughter');
    wx.reLaunch({ url: '/pages/daughter/home/home' });
  },

  chooseCommunity() {
    wx.setStorageSync('role', 'community');
    wx.reLaunch({ url: '/pages/community/home/home' });
  }
});
