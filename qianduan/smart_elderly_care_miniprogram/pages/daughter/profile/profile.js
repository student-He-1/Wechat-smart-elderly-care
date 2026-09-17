// daughter/profile.js
Page({
  data: {
    fields: [
      { key: 'name', label: '姓名', value: '李女士', placeholder: '请输入姓名' },
      { key: 'relation', label: '与老人关系', value: '女儿', placeholder: '请输入关系' },
      { key: 'phone', label: '手机号', value: '138****1234', placeholder: '请输入手机号' },
      { key: 'city', label: '城市', value: '天津', placeholder: '请输入城市' },
      { key: 'elder', label: '绑定老人', value: '张奶奶（母亲）', placeholder: '请输入绑定老人' }
    ]
  },
  onEdit(e) {
    const key = e.currentTarget.dataset.key;
    const value = e.detail.value;
    const fields = this.data.fields.map(f => f.key === key ? { ...f, value } : f);
    this.setData({ fields });
  },
  save() {
    wx.showToast({ title: '已保存', icon: 'success' });
    setTimeout(() => wx.navigateBack(), 800);
  }
});
