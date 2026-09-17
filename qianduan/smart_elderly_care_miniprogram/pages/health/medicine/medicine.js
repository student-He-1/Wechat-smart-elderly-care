// medicine.js
const request = require('../../../utils/request.js')

Page({
  data: {
    medicines: [],
    showModal: false,
    isEdit: false,
    currentMedicineId: null,
    formData: {
      name: '',
      dosage: '',
      time: ''
    }
  },

  onLoad() {
    // 页面加载时获取药品列表
    this.loadMedicines()
  },

  onShow() {
    // 页面显示时刷新药品列表
    this.loadMedicines()
  },

  // 加载药品列表
  loadMedicines() {
    request.get('/medicine').then(res => {
      if (res.message === '获取药品列表成功') {
        this.setData({
          medicines: res.data
        })
      }
    }).catch(err => {
      console.error('获取药品列表失败:', err)
    })
  },

  // 显示添加药品弹窗
  showAddMedicineModal() {
    this.setData({
      showModal: true,
      isEdit: false,
      currentMedicineId: null,
      formData: {
        name: '',
        dosage: '',
        time: ''
      }
    })
  },

  // 显示编辑药品弹窗
  editMedicine(e) {
    const id = e.currentTarget.dataset.id
    const medicine = this.data.medicines.find(item => item.id === id)
    if (medicine) {
      this.setData({
        showModal: true,
        isEdit: true,
        currentMedicineId: id,
        formData: {
          name: medicine.name,
          dosage: medicine.dosage,
          time: medicine.time
        }
      })
    }
  },

  // 隐藏弹窗
  hideModal() {
    this.setData({
      showModal: false
    })
  },

  // 输入框绑定
  bindInput(e) {
    const field = e.currentTarget.dataset.field
    const value = e.detail.value
    this.setData({
      [`formData.${field}`]: value
    })
  },

  // 提交表单
  submitForm() {
    const { name, dosage, time } = this.data.formData
    
    // 表单验证
    if (!name || !dosage || !time) {
      wx.showToast({
        title: '请填写完整信息',
        icon: 'none'
      })
      return
    }

    if (this.data.isEdit) {
      // 编辑药品
      // 注意：后端API暂不支持编辑功能，这里仅做演示
      wx.showToast({
        title: '编辑功能暂未实现',
        icon: 'none'
      })
      this.hideModal()
    } else {
      // 添加药品
      request.post('/medicine', this.data.formData).then(res => {
        if (res.message === '药品添加成功') {
          wx.showToast({
            title: '药品添加成功',
            icon: 'success'
          })
          this.hideModal()
          this.loadMedicines()
        }
      }).catch(err => {
        console.error('添加药品失败:', err)
        wx.showToast({
          title: '添加失败，请重试',
          icon: 'none'
        })
      })
    }
  },

  // 删除药品
  deleteMedicine(e) {
    const id = e.currentTarget.dataset.id
    
    wx.showModal({
      title: '确认删除',
      content: '确定要删除这个药品吗？',
      success: (res) => {
        if (res.confirm) {
          request.delete(`/medicine/${id}`).then(res => {
            if (res.message === '药品删除成功') {
              wx.showToast({
                title: '药品删除成功',
                icon: 'success'
              })
              this.loadMedicines()
            }
          }).catch(err => {
            console.error('删除药品失败:', err)
            wx.showToast({
              title: '删除失败，请重试',
              icon: 'none'
            })
          })
        }
      }
    })
  }
});
