// detail.js —— 个人资料二级页
Page({
  data: {
    profile: {
      name: '张爷爷',
      age: '72 岁',
      gender: '男',
      phone: '138****8888',
      address: '天津市南开区'
    }
  },

  onLoad() {
    // 从 storage 读 profile 页保存的数据
    const saved = wx.getStorageSync('profile');
    if (saved) {
      this.setData({ profile: { ...this.data.profile, ...saved } });
    }
  },

  // 点某一行 → 弹可输入框
  editField(e) {
    const { key, label } = e.currentTarget.dataset;
    const currentValue = this.data.profile[key];

    wx.showModal({
      title: `编辑${label}`,
      editable: true,
      placeholderText: `请输入${label}`,
      content: currentValue,
      success: (res) => {
        if (res.confirm && res.content && res.content.trim()) {
          const next = { ...this.data.profile, [key]: res.content.trim() };
          this.setData({ profile: next });
          wx.setStorageSync('profile', next);
          wx.showToast({ title: '已保存', icon: 'success' });
        }
      }
    });
  }
});
