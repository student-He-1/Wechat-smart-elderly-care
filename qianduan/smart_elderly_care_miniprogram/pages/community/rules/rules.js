// community/rules.js
const { RULES } = require('../../../services/community.js');
Page({
  data: { list: RULES },
  openDetail(e) {
    wx.navigateTo({ url: '/pages/community/rules/detail/detail?id=' + e.currentTarget.dataset.id });
  }
});
