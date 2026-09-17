// health/consult.js
Page({
  data: {
    myCount: 0,
    doctors: [
      { id: 1, name: '利奥波德', title: '主任医师', avatar: '/assets/images/2-4.jpg' },
      { id: 2, name: '海勒', title: '副主任医师', avatar: '/assets/images/2-5.jpg' },
      { id: 3, name: '霍前', title: '主治医师', avatar: '/assets/images/2-6.jpg' },
      { id: 4, name: '张明明', title: '主治医师', avatar: '/assets/images/2-7.jpg' }
    ],
    qaList: [
      { id: 1, user: '睡个好觉', text: '我妈最近血压有点高，头晕，需要去医院吗？大概吃什么药？', time: '2天前', replies: 3 },
      { id: 2, user: '像风一样自由', text: '老人不爱吃饭，吃不下东西怎么办？', time: '3天前', replies: 2 },
      { id: 3, user: '被遗弃的猫', text: '我爸失眠严重，医生建议吃安眠药，具体怎么吃？有副作用吗？', time: '5天前', replies: 1 }
    ]
  },

  askNew() {
    wx.showModal({
      title: '我要问诊',
      editable: true,
      placeholderText: '描述您的症状...',
      success: (res) => {
        if (res.confirm && res.content) {
          const newQ = {
            id: Date.now(),
            user: '我',
            text: res.content,
            time: '刚刚',
            replies: 0
          };
          this.setData({
            qaList: [newQ].concat(this.data.qaList),
            myCount: this.data.myCount + 1
          });
          wx.showToast({ title: '已提交，请等待医生回复', icon: 'none' });
        }
      }
    });
  },

  askMine() {
    wx.showToast({ title: '我的提问（演示）', icon: 'none' });
  },

  openDoctor(e) {
    const { name, avatar } = e.currentTarget.dataset;
    wx.navigateTo({ url: '/pages/health/consult/doctor/doctor?name=' + name + '&avatar=' + (avatar || '') });
  }
});
