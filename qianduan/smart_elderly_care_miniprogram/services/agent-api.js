// agent-api.js —— 健康智能体 / 语音 接口封装
const { post, upload } = require('../utils/request');
const { currentIdentity, BASE_URL } = require('../utils/config');

/**
 * 健康智能体对话（后端 Agent：RAG + 工具查真实数据 + 多轮）
 * @param {object} p { question, sessionId, askerRole, elderId }
 * @returns {Promise<object>} { answer, session_id, is_emergency, tool_traces, rag_refs }
 */
function healthChat({ question, sessionId = null, askerRole, elderId }) {
  const identity = currentIdentity();
  return post('/health-agent/chat', {
    question,
    session_id: sessionId,
    asker_role: askerRole || identity.backendRole,
    elder_id: elderId || identity.userId
  }, { hideError: true }).then((body) => body.data);
}

/**
 * 语音识别：上传录音，返回文字
 * @param {string} filePath 录音临时路径
 * @param {string} dialect 方言
 * @param {string} format 音频格式 wav/mp3
 * @returns {Promise<object>} { text, heard, dialect }
 */
function recognizeVoice(filePath, dialect = 'mandarin', format = 'wav') {
  return upload('/asr', filePath, 'audio', {
    dialect,
    sample_rate: 16000,
    audio_format: format
  }).then((body) => body.data);
}

/**
 * 语音合成：文字 -> 方言 mp3 URL
 * @returns {Promise<string>} audio_url
 */
function synthesize(text, dialect = 'mandarin') {
  return post('/tts', { text, dialect }, { hideError: true })
    .then((body) => body.data.audio_url);
}

function openBranch({ parentSessionId, term, askerRole, elderId }) {
  const identity = currentIdentity();
  return post('/health-agent/branch', {
    parent_session_id: parentSessionId,
    term,
    asker_role: askerRole || identity.backendRole,
    elder_id: elderId || identity.userId
  }, { hideError: true }).then((body) => body.data);
}

/**
 * 流式对话：逐字回调。onDelta(text) 收到增量，onEnd(meta) 收到最终元信息(session_id/terms...)
 */
function healthChatStream({ question, sessionId, askerRole, elderId, branchTerm, onDelta, onReasoning, onEnd, onError }) {
  const identity = currentIdentity()
  const body = {
    question,
    session_id: sessionId || null,
    asker_role: askerRole || identity.backendRole,
    elder_id: elderId || identity.userId,
    branch_term: branchTerm || null
  }
  const req = wx.request({
    url: BASE_URL + '/health-agent/chat/stream',
    method: 'POST',
    data: body,
    enableChunked: true,
    responseType: 'text',
    fail: (err) => { if (!req._manualAbort) { onError && onError(err) } }
  })
  req._manualAbort = false
  const decoder = (typeof TextDecoder !== 'undefined') ? new TextDecoder('utf-8') : null
  let buffer = ''
  req.onChunkReceived((res) => {
    let chunk = ''
    if (decoder) {
      chunk = decoder.decode(res.data, { stream: true })
    } else {
      chunk = '' + res.data
    }
    buffer += chunk
    let idx
    while ((idx = buffer.indexOf('\n\n')) >= 0) {
      const frame = buffer.slice(0, idx)
      buffer = buffer.slice(idx + 2)
      const line = frame.trim()
      if (!line || line.indexOf('data:') !== 0) continue
      const jsonStr = line.slice(5).trim()
      if (!jsonStr) continue
      try {
        const ev = JSON.parse(jsonStr)
        if (ev.event === 'reasoning' && onReasoning) onReasoning(ev.text || '')
        else if (ev.event === 'delta' && onDelta) onDelta(ev.text || '')
        else if (ev.event === 'end') {
          req._manualAbort = true
          try { req.abort() } catch (e) {}
          onEnd(ev)
        }
      } catch (e) {}
    }
  })
}

/**
 * 陪伴聊天助手（轻量）：纯闲聊，一次性返回。
 * @param {string} question 用户当前问题
 * @param {Array} history 最近几轮 [{role:'user'|'assistant', content}]
 */
function companionChat(question, history = []) {
  return post('/companion/chat', { question, history })
}

module.exports = {
  healthChat,
  recognizeVoice,
  synthesize,
  openBranch,
  healthChatStream,
  companionChat
};
