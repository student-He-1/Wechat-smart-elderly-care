// health/hospital.js
Page({
  data: {
    city: '天津',
    area: '全部',
    areas: ['全部', '和平区', '南开区', '河西区', '河北区'],
    hospitals: [
      {
        id: 1,
        name: '天津医科大学总医院',
        district: '天津',
        area: '和平区',
        address: '和平区鞍山道 154 号',
        tag: '医保定点',
        phone: '022-60362255',
        img: '/assets/images/5-1.jpg'
      },
      {
        id: 2,
        name: '天津市第一中心医院',
        district: '天津',
        area: '南开区',
        address: '南开区复康路 24 号',
        tag: '医保定点',
        phone: '022-23626600',
        img: '/assets/images/5-2.jpg'
      },
      {
        id: 3,
        name: '天津市胸科医院',
        district: '天津',
        area: '河西区',
        address: '河西区柳林路 14 号',
        tag: '医保定点',
        phone: '022-88181988',
        img: '/assets/images/5-3.jpg'
      },
      {
        id: 4,
        name: '天津市中医药大学一附院',
        district: '天津',
        area: '南开区',
        address: '南开区鞍山西道 314 号',
        tag: '医保定点',
        phone: '022-27432051',
        img: '/assets/images/5-4.jpg'
      }
    ]
  },

  setCity(e) { this.setData({ city: e.currentTarget.dataset.c }); },
  setArea(e) { this.setData({ area: e.currentTarget.dataset.a }); },

  callHospital(e) {
    wx.makePhoneCall({ phoneNumber: e.currentTarget.dataset.phone });
  },

  openDetail(e) {
    const h = this.data.hospitals.find(x => x.id === e.currentTarget.dataset.id);
    if (!h) return;
    wx.showModal({
      title: h.name,
      content: `地址：${h.address}\n电话：${h.phone}\n等级：三级甲等\n\n就医攻略：\n1. 带身份证和医保卡\n2. 提前在公众号挂号\n3. 空腹去，可能要抽血`,
      showCancel: false
    });
  }
});
