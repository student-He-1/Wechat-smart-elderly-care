// community/visit.js
const { VISITS } = require('../../../services/community.js');
Page({
  data: { list: VISITS },
  addVisit() {
    wx.showModal({
      title: '新增探访记录',
      editable: true,
      placeholderText: '输入探访备注',
      success: (res) => {
        if (res.confirm && res.content) {
          const today = new Date();
          const d = `${today.getFullYear()}-${String(today.getMonth()+1).padStart(2,'0')}-${String(today.getDate()).padStart(2,'0')}`;
          const newItem = {
            id: this.data.list.length + 1,
            elder: '张桂兰',
            date: d,
            type: '上门探访',
            note: res.content
          };
          this.setData({ list: [newItem].concat(this.data.list) });
          wx.showToast({ title: '已记录', icon: 'success' });
        }
      }
    });
  }
});
