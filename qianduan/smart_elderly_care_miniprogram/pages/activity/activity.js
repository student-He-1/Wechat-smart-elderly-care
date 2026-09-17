// activity.js
Page({
  data: {
    list: [
      { id: 1, title: '周三上午 · 社区义诊', desc: '免费测血压血糖，医生现场咨询', time: '本周三 09:00-11:00', location: '社区活动中心一楼', tag: '免费', joined: false, img: '/assets/images/3-4.jpg' },
      { id: 2, title: '周五下午 · 书法兴趣班', desc: '零基础可参加，提供笔墨纸砚', time: '本周五 14:00-16:00', location: '社区活动室二楼', tag: '需报名', joined: false, img: '/assets/images/3-3.jpg' },
      { id: 3, title: '周六上午 · 健步走活动', desc: '公园慢跑，适合所有老人参加', time: '本周六 08:30', location: '水上公园东门集合', tag: '免费', joined: false, img: '/assets/images/3-5.jpg' },
      { id: 4, title: '下周二 · 健康知识讲座', desc: '冬季心脑血管疾病预防', time: '下周二 14:00', location: '社区大礼堂', tag: '需报名', joined: false, img: '/assets/images/3-6.jpg' }
    ]
  },

  join(e) {
    const id = e.currentTarget.dataset.id;
    const list = this.data.list.map(a => a.id === id ? { ...a, joined: true } : a);
    this.setData({ list });
    wx.showToast({ title: '报名成功', icon: 'success' });
  }
});
