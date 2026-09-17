// community/profile.js
Page({
  data: {
    fields: [
      { key: 'name', label: '姓名', value: '王师傅', placeholder: '请输入姓名' },
      { key: 'jobno', label: '工号', value: 'C10339', placeholder: '请输入工号' },
      { key: 'area', label: '负责区域', value: '南开区鼓楼街道', placeholder: '请输入负责区域' },
      { key: 'entry', label: '入职时间', value: '2024-03-15', placeholder: '请输入入职时间' },
      { key: 'phone', label: '联系电话', value: '138****1234', placeholder: '请输入电话' }
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
