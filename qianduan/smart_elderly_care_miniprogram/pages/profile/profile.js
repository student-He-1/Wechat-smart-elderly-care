// profile.js
Page({
  data: {
    isLoggedIn: true,
    nightMode: false,
    profile: {
      name: '张奶奶',
      age: '70 岁',
      gender: '女',
      phone: '138****8888',
      address: '天津市南开区'
    },
    contacts: [
      { name: '张三', relation: '儿子', phone: '13800138000', avatar: '/assets/images/6-1.png' },
      { name: '李四', relation: '女儿', phone: '13900139000', avatar: '/assets/images/6-2.png' }
    ]
  },

  onLoad() {
    // 页面加载时的初始化
    console.log('我的页面加载');
  },

  onShow() {
    // 从二级页编辑回来后，同步最新 profile
    const saved = wx.getStorageSync('profile');
    if (saved) {
      this.setData({ profile: { ...this.data.profile, ...saved } });
    }
    // 同步夜间模式
    const dark = wx.getStorageSync('dark');
    this.setData({ nightMode: dark });
    // 同步自定义 TabBar 选中态
    if (typeof this.getTabBar === 'function' && this.getTabBar()) {
      this.getTabBar().setData({ selected: 3 });
    }
  },

  // 紧急求助
  emergencySos() {
    wx.showModal({
      title: '紧急求助',
      content: '确定要呼叫紧急联系人吗？',
      confirmText: '立即呼叫',
      confirmColor: '#dc2626',
      success: (res) => {
        if (res.confirm) {
          wx.showToast({
            title: '正在呼叫紧急联系人…',
            icon: 'none'
          });
          setTimeout(() => {
            wx.showToast({
              title: '已通知家人',
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
      fail: () => {
        wx.showToast({
          title: '拨号失败',
          icon: 'none'
        });
      }
    });
  },

  // 登录/退出登录
  login() {
    if (this.data.isLoggedIn) {
      // 退出登录
      wx.showModal({
        title: '退出登录',
        content: '确定要退出登录吗？',
        success: (res) => {
          if (res.confirm) {
            this.setData({
              isLoggedIn: false
            });
            wx.showToast({
              title: '已退出登录',
              icon: 'success'
            });
          }
        }
      });
    } else {
      // 登录
      wx.showModal({
        title: '登录',
        content: '请输入账号密码登录',
        success: (res) => {
          if (res.confirm) {
            this.setData({
              isLoggedIn: true
            });
            wx.showToast({
              title: '登录成功',
              icon: 'success'
            });
          }
        }
      });
    }
  },

  // 导航到提醒设置页面
  navigateToReminderSettings() {
    wx.navigateTo({
      url: '/pages/profile/reminder/reminder'
    });
  },

  // 导航到语音设置页面
  navigateToVoiceSettings() {
    wx.navigateTo({
      url: '/pages/profile/voice/voice'
    });
  },

  // 切换身份
  switchRole() {
    wx.showActionSheet({
      itemList: ['子女端（远程照护）', '社区端（工单处理）'],
      success: (res) => {
        if (res.tapIndex === 0) {
          wx.setStorageSync('role', 'daughter');
          wx.reLaunch({ url: '/pages/daughter/home/home' });
        } else if (res.tapIndex === 1) {
          wx.setStorageSync('role', 'community');
          wx.reLaunch({ url: '/pages/community/home/home' });
        }
      }
    });
  },

  // 关于我们
  navigateToAbout() {
    wx.showModal({
      title: '关于我们',
      content: '智慧养老小程序 · 演示测试练手项目\n\n本项目仅用于 UI 学习与前端开发练习，所有数据均为模拟，不提供真实医疗服务。\n\n版本 v1.0.0',
      showCancel: false,
      confirmText: '知道了'
    });
  },

  // 切换夜间模式
  toggleNightMode(e) {
    const v = e.detail.value;
    this.setData({ nightMode: v });
    wx.setStorageSync('dark', v);
    wx.showToast({
      title: v ? '已开启夜间模式' : '已关闭夜间模式',
      icon: 'success'
    });
  },

  // 编辑个人信息（真能输入，改完即时更新）
  editInfo(e) {
    const label = e.currentTarget.dataset.label;
    this._openEditModal(label);
  },

  // 深蓝卡"服务权益"：展示已开通的服务包
  showBenefits() {
    wx.showActionSheet({
      itemList: [
        '✓ 紧急监护（已开通）',
        '✓ 用药提醒（已开通）',
        '✓ 健康咨询（已开通）',
        '+ 更多服务（开发中）'
      ],
      success: (res) => {
        if (res.tapIndex === 3) {
          wx.showToast({ title: '更多服务即将上线', icon: 'none' });
        }
      }
    });
  },

  // 顶部"点击查看个人资料"：选编辑哪一项
  editProfile() {
    wx.showActionSheet({
      itemList: ['姓名', '年龄', '性别', '联系电话', '居住地址'],
      success: (res) => {
        this._openEditModal(['姓名', '年龄', '性别', '联系电话', '居住地址'][res.tapIndex]);
      }
    });
  },

  // 打开可输入弹窗
  _openEditModal(label) {
    const map = {
      '姓名': 'name',
      '年龄': 'age',
      '性别': 'gender',
      '联系电话': 'phone',
      '居住地址': 'address'
    };
    const currentKey = map[label] || 'name';
    const currentValue = this.data.profile[currentKey];

    wx.showModal({
      title: `编辑${label}`,
      editable: true,
      placeholderText: `请输入${label}`,
      content: currentValue,
      success: (res) => {
        if (res.confirm && res.content && res.content.trim()) {
          this.setData({
            [`profile.${currentKey}`]: res.content.trim()
          });
          wx.showToast({ title: '已保存', icon: 'success' });
        }
      }
    });
  }
});
