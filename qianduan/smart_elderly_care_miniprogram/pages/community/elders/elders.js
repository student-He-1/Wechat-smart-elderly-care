// community/elders.js
Page({
  data: {
    elders: [
      { id: 1, name: '张桂兰', age: 78, chronic: '高血压', family: '儿子 138****1234', phone: '138****1234', avatar: '/assets/images/6-3.png' },
      { id: 2, name: '李建国', age: 82, chronic: '糖尿病', family: '女儿 139****5678', phone: '139****5678', avatar: '/assets/images/6-4.png' },
      { id: 3, name: '王秀珍', age: 76, chronic: '冠心病', family: '儿子 137****9012', phone: '137****9012', avatar: '/assets/images/6-5.png' }
    ]
  },
  call(e) { wx.makePhoneCall({ phoneNumber: e.currentTarget.dataset.phone }); },
  goHome() { wx.reLaunch({ url: '/pages/community/home/home' }); },
  goAlert() { wx.reLaunch({ url: '/pages/community/alert/alert' }); },
  goElders() { wx.reLaunch({ url: '/pages/community/elders/elders' }); },
  goMine() { wx.reLaunch({ url: '/pages/community/mine/mine' }); }
});
