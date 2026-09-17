// contact.js
Page({
  data: {
    contacts: [
      {
        name: '张三',
        relation: '儿子',
        phone: '13800138000'
      },
      {
        name: '李四',
        relation: '女儿',
        phone: '13900139000'
      }
    ],
    showModal: false,
    formData: {
      name: '',
      relation: '',
      phone: ''
    }
  },

  onLoad() {
    // 页面加载时的初始化
    console.log('联系页面加载');
  },

  // 紧急呼叫
  emergencyCall() {
    wx.showModal({
      title: '紧急呼叫',
      content: '确定要拨打紧急求助电话吗？',
      success: (res) => {
        if (res.confirm) {
          // 模拟紧急呼叫
          wx.showToast({
            title: '正在呼叫紧急联系人...',
            icon: 'none'
          });
          setTimeout(() => {
            wx.showToast({
              title: '呼叫成功',
              icon: 'success'
            });
          }, 2000);
        }
      }
    });
  },

  // 呼叫联系人
  callContact(e) {
    const phone = e.currentTarget.dataset.phone;
    wx.makePhoneCall({
      phoneNumber: phone,
      success: function() {
        console.log('拨打电话成功');
      },
      fail: function() {
        console.log('拨打电话失败');
      }
    });
  },

  // 发送消息
  messageContact(e) {
    const { phone, name } = e.currentTarget.dataset;
    wx.navigateTo({
      url: `/pages/contact/chat/chat?phone=${phone}&name=${name}`
    });
  },

  // 显示添加联系人弹窗
  showAddContactModal() {
    this.setData({
      showModal: true,
      formData: {
        name: '',
        relation: '',
        phone: ''
      }
    });
  },

  // 隐藏弹窗
  hideModal() {
    this.setData({
      showModal: false
    });
  },

  // 输入框绑定
  bindInput(e) {
    const field = e.currentTarget.dataset.field;
    const value = e.detail.value;
    this.setData({
      [`formData.${field}`]: value
    });
  },

  // 添加联系人
  addContact() {
    const { name, relation, phone } = this.data.formData;
    
    // 表单验证
    if (!name || !relation || !phone) {
      wx.showToast({
        title: '请填写完整信息',
        icon: 'none'
      });
      return;
    }

    // 添加联系人
    const newContact = {
      name: name,
      relation: relation,
      phone: phone
    };
    
    this.setData({
      contacts: [...this.data.contacts, newContact],
      showModal: false
    });
    
    wx.showToast({
      title: '联系人添加成功',
      icon: 'success'
    });
  }
});
