// news/detail.js
const { NEWS } = require('../../../services/news.js');

Page({
  data: { item: {} },
  onLoad(opt) {
    const id = parseInt(opt.id);
    const item = NEWS.find(n => n.id === id) || NEWS[0];
    this.setData({ item });
    wx.setNavigationBarTitle({ title: item.source });
  }
});
