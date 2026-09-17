// pages/companion/album/album.js —— 家庭相册
const { PHOTOS } = require('../../../utils/album-config');

Page({
  data: {
    photos: PHOTOS,
    showPreview: false,
    previewIndex: 0,
  },

  // 点击查看大图
  previewPhoto(e) {
    const index = e.currentTarget.dataset.index;
    this.setData({ showPreview: true, previewIndex: index });
  },

  // 滑动切换
  onSwiperChange(e) {
    this.setData({ previewIndex: e.detail.current });
  },

  // 关闭预览
  closePreview() {
    this.setData({ showPreview: false });
  },

  // 阻止冒泡
  stopPropagation() {},
});
