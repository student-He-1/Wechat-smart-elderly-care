// daughter/services.js
Page({
  data: {
    type: 'all',
    area: '全部',
    areas: ['全部', '和平区', '南开区', '河西区', '河北区'],
    orgs: [
      { id: 1, name: '天津康乐园养老院', type: '养老机构', score: 4.8, address: '南开区鼓楼西街 12 号', area: '南开区', phone: '022-2730xxxx', img: '/assets/images/7-1.png' },
      { id: 2, name: '安心保洁服务中心', type: '保洁', score: 4.6, address: '和平区南京路 88 号', area: '和平区', phone: '022-2305xxxx', img: '/assets/images/7-2.png' },
      { id: 3, name: '颐家护理站', type: '护理', score: 4.9, address: '河西区友谊路 21 号', area: '河西区', phone: '022-2835xxxx', img: '/assets/images/7-3.png' },
      { id: 4, name: '陪诊小哥·专业陪诊', type: '陪诊', score: 4.7, address: '河北区中山路 150 号', area: '河北区', phone: '022-2628xxxx', img: '/assets/images/7-4.png' }
    ]
  },

  setType(e) { this.setData({ type: e.currentTarget.dataset.t }); },
  setArea(e) { this.setData({ area: e.currentTarget.dataset.a }); },

  callOrg(e) {
    const phone = e.currentTarget.dataset.phone;
    wx.makePhoneCall({ phoneNumber: phone });
  },

  goHome() { wx.reLaunch({ url: '/pages/daughter/home/home' }); },
  goAlerts() { wx.reLaunch({ url: '/pages/daughter/alerts/alerts' }); },
  goServices() { wx.reLaunch({ url: '/pages/daughter/services/services' }); },
  goMine() { wx.reLaunch({ url: '/pages/daughter/mine/mine' }); }
});
