// services/orders.js —— 工单数据（演示用）
// status: pending(待接单) | ontheway(出发中) | serving(服务中) | done(已完成)
const ORDERS = [
  {
    id: 'O20260913001',
    elderName: '张奶奶',
    elderPhone: '138****1234',
    serviceType: '上门保洁',
    address: '南开区鼓楼西街 12 号 3-201',
    bookTime: '今天 14:00',
    status: 'pending',
    remark: '重点清洁厨房和卫生间',
    price: '80元'
  },
  {
    id: 'O20260913002',
    elderName: '李大爷',
    elderPhone: '139****5678',
    serviceType: '陪诊就医',
    address: '和平区南京路 88 号',
    bookTime: '明天 08:30',
    status: 'pending',
    remark: '去市总医院复查高血压',
    price: '150元'
  },
  {
    id: 'O20260912008',
    elderName: '王奶奶',
    elderPhone: '137****9012',
    serviceType: '助餐配送',
    address: '河西区友谊路 21 号',
    bookTime: '今天 11:30',
    status: 'ontheway',
    remark: '低盐低脂套餐',
    price: '25元'
  }
];

module.exports = { ORDERS };
