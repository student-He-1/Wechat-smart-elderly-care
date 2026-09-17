// alert-api.js —— 合并「后端真实告警（跌倒/SOS 等）」与「本地模拟告警」，供子女/社区端展示
const { get, post } = require('../utils/request')
const { BASE_URL } = require('../utils/config')
// 主后端站点根地址（用于拼接 /static 截图 URL）
const ORIGIN = BASE_URL.replace(/\/api$/, '')

const TYPE_TEXT = {
  fall: '检测到跌倒',
  sos: '紧急求助',
  medicine: '用药提醒',
  bp: '血压异常',
  glucose: '血糖异常',
  inactive: '久未活动'
}

// 后端 created_at 为 UTC（无时区后缀），补 Z 后转成本地时间展示
function fmtTime(iso) {
  if (!iso) return ''
  const d = new Date(iso.includes('Z') ? iso : iso + 'Z')
  if (isNaN(d.getTime())) return ''
  const p = (n) => String(n).padStart(2, '0')
  const hm = `${p(d.getHours())}:${p(d.getMinutes())}`
  const sameDay = d.toDateString() === new Date().toDateString()
  return sameDay ? `今天 ${hm}` : `${d.getMonth() + 1}月${d.getDate()}日 ${hm}`
}

function mapOne(a) {
  return {
    id: 'srv_' + a.id,
    serverId: a.id,
    title: a.detail || TYPE_TEXT[a.type] || '告警',
    time: fmtTime(a.created_at),
    level: a.level === 'urgent' ? 'urgent' : 'normal',
    handled: !!a.status && a.status !== 'unhandled',
    type: a.type,
    snapshotUrl: a.snapshot_url ? ORIGIN + a.snapshot_url : ''
  }
}

/**
 * 拉取后端告警并与本地 storage 告警合并。
 * 后端项以 srv_ 前缀，每次以服务端为准；本地模拟项保留。
 * @returns {Promise<Array>}
 */
function loadAlerts() {
  const local = wx.getStorageSync('alerts') || []
  return get('/alerts', { hideError: true }).then((body) => {
    let server = (body.data || []).map(mapOne)
    // 子女端不展示「血压电话回访」这类社区内部处理记录（只在社区端保留）
    if (wx.getStorageSync('role') === 'daughter') {
      server = server.filter((a) => a.type !== 'bp_high')
    }
    const localOnly = local.filter((a) => !String(a.id).startsWith('srv_'))
    // 后端已按时间倒序，放前面；本地模拟项跟在后面
    return server.concat(localOnly)
  }).catch(() => local)
}

// 处理一条告警：后端项调接口，本地项由调用方自行写 storage
function handleServerAlert(item) {
  if (item && item.serverId) {
    // 后端 AlertHandle 的 handler_id 必填（演示阶段处理人统一用 2=家属/社区）
    return post(`/alerts/${item.serverId}/handle`, { action: 'handled', handler_id: 2 }, { hideError: true })
  }
  return Promise.resolve()
}

// 跌倒记录（监控页用）：拉全部 fall 告警，含现场截图与时间
function listFallRecords() {
  return get('/alerts', { data: { type: 'fall' }, hideError: true })
    .then((body) => (body.data || []).map(mapOne))
    .catch(() => [])
}

module.exports = { loadAlerts, handleServerAlert, listFallRecords, TYPE_TEXT }
