// daughter/order.js
Page({
  data: {
    services: [
      { id: 1, name: '助餐', price: '25' },
      { id: 2, name: '陪诊', price: '120' },
      { id: 3, name: '保洁', price: '80' },
      { id: 4, name: '维修', price: '60' }
    ],
    selectedService: 1,
    selectedPrice: '25',
    date: '2026-09-14',
    time: '09:00'
  },

  selectService(e) {
    const id = e.currentTarget.dataset.id;
    const s = this.data.services.find(x => x.id === id);
    this.setData({ selectedService: id, selectedPrice: s.price });
  },

  onDateChange(e) { this.setData({ date: e.detail.value }); },
  onTimeChange(e) { this.setData({ time: e.detail.value }); },

  submitOrder() {
    wx.showModal({
      title: '确认代付',
      content: '将为妈妈预约服务并完成支付，确认下单吗？',
      confirmText: '确认支付',
      success: (res) => {
        if (res.confirm) {
          wx.showToast({ title: '下单成功', icon: 'success' });
          setTimeout(() => wx.navigateBack(), 1200);
        }
      }
    });
  }
});
