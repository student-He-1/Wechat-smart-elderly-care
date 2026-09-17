// news/index.js
const { NEWS } = require('../../services/news.js');

Page({
  data: { list: NEWS },
  openDetail(e) {
    wx.navigateTo({ url: '/pages/news/detail/detail?id=' + e.currentTarget.dataset.id });
  }
});
