// custom-tab-bar/index.js
Component({
  data: {
    selected: 0,
    list: [
      { pagePath: '/pages/index/index', text: '首页', icon: 'ic-home', iconOn: 'ic-home-on' },
      { pagePath: '/pages/health/main/main', text: '健康', icon: 'ic-health', iconOn: 'ic-health-on' },
      { pagePath: '/pages/chat/chat', text: '陪伴', icon: 'ic-companion', iconOn: 'ic-companion-on' },
      { pagePath: '/pages/profile/profile', text: '我的', icon: 'ic-me', iconOn: 'ic-me-on' }
    ]
  },
  methods: {
    switchTab(e) {
      const index = e.currentTarget.dataset.index
      wx.switchTab({ url: this.data.list[index].pagePath })
    }
  }
})
