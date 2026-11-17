/**
 * app.js — OTA Support Web UI
 * Handles: welcome screen, chat, call state machine (fixed),
 *          history, feedback, stats, report download, audio recording
 */

// ══════════════════════════════════════════════════════
// STATE
// ══════════════════════════════════════════════════════
const state = {
  mode:              'chat',
  callActive:        false,
  callSeconds:       0,
  callTimer:         null,
  callStartTimeout:  null,   // setTimeout handle for the "connecting" delay
  typewriterIv:      null,   // setInterval handle for transcript typewriter
  muted:             false,
  speakerOn:         true,
  starRating:        0,
  sessions:          0,
  resolved:          0,
  history:           [],     // { id, snippet, time, type, status }
  chatLog:           [],     // { role, text, time } — for report export
  callTranscriptText:'',     // captured transcript text for the report
  mediaRecorder:     null,
  audioChunks:       [],
};

// ══════════════════════════════════════════════════════
// DOM REFS
// ══════════════════════════════════════════════════════
const $ = id => document.getElementById(id);

const welcomeScreen   = $('welcome-screen');
const appWrapper      = $('app-wrapper');
const btnEnter        = $('btn-enter');

const chatMessages    = $('chat-messages');
const chatInput       = $('chat-input');
const btnSend         = $('btn-send');
const btnChatMode     = $('btn-chat-mode');
const btnCallMode     = $('btn-call-mode');
const panelChat       = $('panel-chat');
const panelCall       = $('panel-call');
const btnCallToggle   = $('btn-call-toggle');
const callIcon        = $('call-icon');
const callStateLabel  = $('call-state-label');
const callTimerEl     = $('call-timer');
const callAvatarRing  = $('call-avatar-ring');
const waveform        = $('waveform');
const callTranscript  = $('call-transcript');
const btnMute         = $('btn-mute');
const btnSpeaker      = $('btn-speaker');
const btnDownloadCall = $('btn-download-call');
const historyList     = $('history-list');
const historyEmpty    = $('history-empty');
const btnClearHistory = $('btn-clear-history');
const starsRow        = $('stars-row');
const feedbackText    = $('feedback-text');
const btnSubmitFb     = $('btn-submit-feedback');
const feedbackConfirm = $('feedback-confirm');
const statSessions    = $('stat-sessions');
const statResolved    = $('stat-resolved');
const statRating      = $('stat-rating');
const quickActions    = $('quick-actions');
const btnExportChat   = $('btn-export-chat');
const toastEl         = $('toast');

// ══════════════════════════════════════════════════════
// WELCOME SCREEN
// ══════════════════════════════════════════════════════
btnEnter.addEventListener('click', () => {
  welcomeScreen.classList.add('fade-out');
  // Show app simultaneously
  appWrapper.style.display = 'flex';
  setTimeout(() => {
    welcomeScreen.style.display = 'none';
  }, 650);
});

// ══════════════════════════════════════════════════════
// TOAST
// ══════════════════════════════════════════════════════
let toastTimeout = null;
function showToast(msg, duration = 3000) {
  toastEl.textContent = msg;
  toastEl.classList.add('show');
  clearTimeout(toastTimeout);
  toastTimeout = setTimeout(() => toastEl.classList.remove('show'), duration);
}

// ══════════════════════════════════════════════════════
// UTILITY
// ══════════════════════════════════════════════════════
function nowTime() {
  return new Date().toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' });
}
function nowFull() {
  return new Date().toLocaleString('en-GB', {
    day:'2-digit', month:'short', year:'numeric',
    hour:'2-digit', minute:'2-digit', second:'2-digit'
  });
}
function formatSeconds(s) {
  const m   = String(Math.floor(s / 60)).padStart(2, '0');
  const sec = String(s % 60).padStart(2, '0');
  return `${m}:${sec}`;
}
function uid() {
  return Math.random().toString(36).slice(2, 9);
}

// ══════════════════════════════════════════════════════
// FILE DOWNLOAD HELPER
// ══════════════════════════════════════════════════════
function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a   = document.createElement('a');
  a.href     = url;
  a.download  = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

// ══════════════════════════════════════════════════════
// CHAT REPORT EXPORT
// ══════════════════════════════════════════════════════
function exportChatReport() {
  if (!state.chatLog.length) {
    showToast('No conversation to export yet.');
    return;
  }
  const lines = state.chatLog.map(m =>
    `[${m.time}]  ${m.role === 'agent' ? 'OTA Support' : 'You'}: ${m.text}`
  ).join('\n');

  const report = [
    'OTA SUPPORT — CONVERSATION REPORT',
    '═'.repeat(50),
    `Generated  : ${nowFull()}`,
    `Agent      : OTA Support AI (Powered by AntiGravity AI)`,
    `Channel    : Chat`,
    `Sessions   : ${state.sessions}`,
    `Resolved   : ${state.resolved} / ${state.sessions}`,
    `Rating     : ${state.starRating > 0 ? state.starRating + '/5 stars' : 'Not rated'}`,
    '═'.repeat(50),
    'CONVERSATION TRANSCRIPT',
    '─'.repeat(50),
    lines,
    '─'.repeat(50),
    '',
    'OTA Support v1.0 — Confidential — AntiGravity AI',
  ].join('\n');

  const blob = new Blob([report], { type: 'text/plain;charset=utf-8' });
  downloadBlob(blob, `ota-chat-report-${Date.now()}.txt`);
  showToast('✓ Chat report downloaded');
}

btnExportChat.addEventListener('click', exportChatReport);

// ══════════════════════════════════════════════════════
// CALL REPORT EXPORT
// ══════════════════════════════════════════════════════
function exportCallReport(durationSecs) {
  const dur = formatSeconds(durationSecs);
  const report = [
    'OTA SUPPORT — CALL REPORT',
    '═'.repeat(50),
    `Generated  : ${nowFull()}`,
    `Duration   : ${dur}`,
    `Agent      : OTA Support AI (Powered by AntiGravity AI)`,
    `Channel    : Voice Call`,
    '═'.repeat(50),
    'LIVE TRANSCRIPT',
    '─'.repeat(50),
    state.callTranscriptText || 'No transcript captured.',
    '─'.repeat(50),
    '',
    'OTA Support v1.0 — Confidential — AntiGravity AI',
  ].join('\n');

  const blob = new Blob([report], { type: 'text/plain;charset=utf-8' });
  downloadBlob(blob, `ota-call-report-${Date.now()}.txt`);
  showToast('✓ Call report downloaded');
}

btnDownloadCall.addEventListener('click', () => {
  exportCallReport(state.callSeconds);
});

// ══════════════════════════════════════════════════════
// AUDIO RECORDING (via MediaRecorder API)
// ══════════════════════════════════════════════════════
async function startAudioRecording() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    state.mediaRecorder = new MediaRecorder(stream);
    state.audioChunks   = [];
    state.mediaRecorder.ondataavailable = e => {
      if (e.data.size > 0) state.audioChunks.push(e.data);
    };
    state.mediaRecorder.start();
    console.log('[OTA] Audio recording started');
  } catch (err) {
    console.log('[OTA] Microphone not available:', err.message);
    state.mediaRecorder = null;
  }
}

function stopAudioRecording() {
  return new Promise(resolve => {
    if (!state.mediaRecorder || state.mediaRecorder.state === 'inactive') {
      resolve(null);
      return;
    }
    state.mediaRecorder.onstop = () => {
      const blob = new Blob(state.audioChunks, { type: 'audio/webm' });
      // Stop all mic tracks
      state.mediaRecorder.stream.getTracks().forEach(t => t.stop());
      state.mediaRecorder = null;
      resolve(blob);
    };
    state.mediaRecorder.stop();
  });
}

// ══════════════════════════════════════════════════════
// DEMO AI RESPONSES
// ══════════════════════════════════════════════════════
const DEMO_RESPONSES = {
  'check my bill': [
    "I can pull up your billing summary. Your current balance is DZD 2,400, due on the 20th. Would you like a breakdown of charges?",
    "Your last bill was DZD 2,400. I see no unusual charges. Is there a specific item you'd like me to explain?"
  ],
  'internet is slow': [
    "I'm sorry to hear that. A quick line check shows you're getting 18 Mbps of your 50 Mbps plan. Try rebooting your router — unplug it for 30 seconds. Let me know if that helps!",
    "Slow connectivity can have several causes. Signal quality appears slightly degraded in your area. Our engineers are working on it. Expected resolution: within 2 hours."
  ],
  'reset my router': [
    "Press and hold the reset button on the back of your router for 10 seconds until the lights blink. Then wait 2 minutes for it to reconnect. Let me know if that works!",
    "Hold the small reset button for 10 seconds. The router will restart automatically. Your default Wi-Fi credentials are printed on the label underneath the device."
  ],
  'cancel subscription': [
    "Before I process this, may I ask if there's an issue we can resolve? If you still wish to cancel, your service will remain active until the end of your billing cycle.",
    "Your subscription is currently on the Premium Plan at DZD 3,200/month. Would you like to downgrade instead, or confirm full cancellation?"
  ],
  'talk to a human': [
    "Of course! Connecting you to a live agent now. Average wait time is under 2 minutes. Please hold...",
    "Transferring you to our specialist team. You'll receive an SMS confirmation shortly. Is there anything else I can note for the agent?"
  ],
  'default': [
    "Thank you for reaching out to OTA Support! I'm looking into that for you. Could you provide a bit more detail so I can assist you better?",
    "I've noted your query and I'm checking our knowledge base. Based on what you've described, here's what I can help you with today.",
    "Great question! Let me pull up the relevant information for your account. This will just take a moment.",
    "I understand how important this is. Let me make sure I get this right for you.",
    "I've checked our system and here's what I found. Is there anything specific you'd like me to clarify?"
  ]
};

function getDemoResponse(input) {
  const lower = input.toLowerCase().trim();
  for (const [key, replies] of Object.entries(DEMO_RESPONSES)) {
    if (key !== 'default' && lower.includes(key)) {
      return replies[Math.floor(Math.random() * replies.length)];
    }
  }
  const d = DEMO_RESPONSES.default;
  return d[Math.floor(Math.random() * d.length)];
}

// ══════════════════════════════════════════════════════
// CHAT — render messages
// ══════════════════════════════════════════════════════
function renderMessage(role, text, time = nowTime()) {
  // Log for report export
  state.chatLog.push({ role, text, time });

  const row = document.createElement('div');
  row.className = `bubble-row ${role}`;

  const avatar = document.createElement('div');
  avatar.className = 'bubble-avatar';
  avatar.textContent = role === 'agent' ? 'OA' : 'ME';

  const bubble = document.createElement('div');
  bubble.className = 'bubble';
  bubble.textContent = text;

  const meta = document.createElement('div');
  meta.className = 'bubble-meta';
  meta.textContent = time;

  const inner = document.createElement('div');
  inner.appendChild(bubble);
  inner.appendChild(meta);

  if (role === 'agent') {
    row.appendChild(avatar);
    row.appendChild(inner);
  } else {
    row.appendChild(inner);
    row.appendChild(avatar);
  }

  chatMessages.appendChild(row);
  chatMessages.scrollTop = chatMessages.scrollHeight;
  return row;
}

function showTyping() {
  const row = document.createElement('div');
  row.className = 'bubble-row agent';
  row.id = 'typing-row';

  const avatar = document.createElement('div');
  avatar.className = 'bubble-avatar';
  avatar.textContent = 'OA';

  const indicator = document.createElement('div');
  indicator.className = 'typing-indicator';
  for (let i = 0; i < 3; i++) {
    const d = document.createElement('div');
    d.className = 'typing-dot';
    indicator.appendChild(d);
  }

  row.appendChild(avatar);
  row.appendChild(indicator);
  chatMessages.appendChild(row);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

function removeTyping() {
  const t = $('typing-row');
  if (t) t.remove();
}

function sendMessage(text) {
  if (!text.trim()) return;

  renderMessage('user', text.trim());
  chatInput.value = '';
  chatInput.style.height = '';

  if (quickActions) quickActions.style.display = 'none';

  showTyping();

  const delay = 800 + Math.random() * 900;
  setTimeout(() => {
    removeTyping();
    const reply = getDemoResponse(text);
    renderMessage('agent', reply);

    addHistoryItem({
      id:      uid(),
      snippet: text.trim().slice(0, 45),
      time:    nowTime(),
      type:    'chat',
      status:  'resolved'
    });
    updateStats(true);
  }, delay);
}

// Auto-resize textarea
chatInput.addEventListener('input', () => {
  chatInput.style.height = 'auto';
  chatInput.style.height = Math.min(chatInput.scrollHeight, 120) + 'px';
});

chatInput.addEventListener('keydown', e => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage(chatInput.value);
  }
});

btnSend.addEventListener('click', () => sendMessage(chatInput.value));

document.querySelectorAll('.quick-btn').forEach(btn => {
  btn.addEventListener('click', () => sendMessage(btn.dataset.msg));
});

// ══════════════════════════════════════════════════════
// MODE SWITCH
// ══════════════════════════════════════════════════════
function switchMode(mode) {
  state.mode = mode;
  btnChatMode.classList.toggle('active', mode === 'chat');
  btnCallMode.classList.toggle('active', mode === 'call');
  btnChatMode.setAttribute('aria-selected', mode === 'chat');
  btnCallMode.setAttribute('aria-selected', mode === 'call');
  panelChat.classList.toggle('hidden', mode !== 'chat');
  panelCall.classList.toggle('hidden', mode !== 'call');
}

btnChatMode.addEventListener('click', () => switchMode('chat'));
btnCallMode.addEventListener('click', () => switchMode('call'));

// ══════════════════════════════════════════════════════
// CALL STATE MACHINE   ← FIXED
// ══════════════════════════════════════════════════════

// Pre-scripted call dialogue — used only by typewriter inside call-transcript
const CALL_SCRIPTS = [
  [
    { speaker: 'OTA Support', text: 'Hello! Thank you for calling OTA Support. How can I help you today?' },
    { speaker: 'Customer',    text: 'Hi, my internet has been dropping since this morning.' },
    { speaker: 'OTA Support', text: 'I understand, that must be frustrating. Let me run a quick diagnostic on your line...' },
    { speaker: 'OTA Support', text: 'I can see some signal instability on your account. Our team has already been notified and is working on it. Expected fix: within 2 hours.' },
    { speaker: 'Customer',    text: 'Okay, thank you!' },
    { speaker: 'OTA Support', text: 'Of course! Is there anything else I can help you with today?' },
  ],
  [
    { speaker: 'OTA Support', text: 'Welcome to OTA Support! My name is OTA and I\'m here to assist you.' },
    { speaker: 'Customer',    text: 'I think I was charged twice on my last bill.' },
    { speaker: 'OTA Support', text: 'I\'m sorry to hear that. Let me verify your billing details right away...' },
    { speaker: 'OTA Support', text: 'You\'re right — I see a duplicate charge of DZD 2,400. A full refund has been initiated. You\'ll receive confirmation by SMS within 24 hours.' },
    { speaker: 'Customer',    text: 'That\'s great, thanks so much!' },
    { speaker: 'OTA Support', text: 'Happy to help! Thank you for contacting OTA Support. Have a wonderful day!' },
  ],
  [
    { speaker: 'OTA Support', text: 'OTA Support, how may I assist you today?' },
    { speaker: 'Customer',    text: 'I\'d like to know the available data plans.' },
    { speaker: 'OTA Support', text: 'We currently offer three plans: Basic at DZD 1,200/mo with 50 GB, Premium at DZD 3,200/mo with unlimited data, and Pro at DZD 2,000/mo with 200 GB.' },
    { speaker: 'Customer',    text: 'What does the Premium plan include?' },
    { speaker: 'OTA Support', text: 'Premium includes unlimited 4G data, free calls, and priority customer support. Would you like me to upgrade your account?' },
    { speaker: 'Customer',    text: 'Let me think about it. Thanks!' },
    { speaker: 'OTA Support', text: 'No problem! Feel free to call us anytime. Have a great day!' },
  ]
];

// ── Typewriter for call transcript ONLY ─────────────
function typeCallScript(lines) {
  // Reset
  callTranscript.textContent = '';
  state.callTranscriptText   = '';
  let lineIdx = 0;
  let charIdx = 0;
  let currentLine = '';

  // Clear any previous interval
  if (state.typewriterIv) {
    clearInterval(state.typewriterIv);
    state.typewriterIv = null;
  }

  state.typewriterIv = setInterval(() => {
    // Stop if call was ended
    if (!state.callActive) {
      clearInterval(state.typewriterIv);
      state.typewriterIv = null;
      return;
    }

    if (lineIdx >= lines.length) {
      clearInterval(state.typewriterIv);
      state.typewriterIv = null;
      return;
    }

    const line = lines[lineIdx];
    const fullLine = `${line.speaker}: ${line.text}`;

    if (charIdx < fullLine.length) {
      currentLine += fullLine[charIdx];
      charIdx++;

      // Update ONLY the call-transcript div
      const existing = state.callTranscriptText;
      callTranscript.textContent = existing + currentLine;
      callTranscript.scrollTop   = callTranscript.scrollHeight;
    } else {
      // Line complete — move to next
      state.callTranscriptText += currentLine + '\n';
      currentLine = '';
      charIdx  = 0;
      lineIdx++;

      if (lineIdx < lines.length) {
        // Brief pause between speakers
        clearInterval(state.typewriterIv);
        state.typewriterIv = null;
        setTimeout(() => {
          if (!state.callActive) return; // abort if call ended during pause
          state.typewriterIv = setInterval(arguments.callee, 22);
        }, 600);
      } else {
        callTranscript.textContent = state.callTranscriptText.trim();
        clearInterval(state.typewriterIv);
        state.typewriterIv = null;
      }
    }
  }, 22);
}

// ── startCall ─────────────────────────────────────────
async function startCall() {
  // Safety: clean up any lingering state
  cleanupCall();

  state.callActive  = true;
  state.callSeconds = 0;
  state.callTranscriptText = '';

  callAvatarRing.classList.add('ringing');
  callStateLabel.textContent  = 'Connecting...';
  callTimerEl.textContent     = '00:00';
  callTranscript.innerHTML    = '<span class="transcript-placeholder">Connecting to OTA Support...</span>';
  btnDownloadCall.classList.add('hidden');

  // Switch button to End Call (red ✕)
  setCallBtn('end');

  // Start microphone recording
  await startAudioRecording();

  // After connecting delay → go live
  state.callStartTimeout = setTimeout(() => {
    if (!state.callActive) return; // user cancelled during connecting

    callStateLabel.textContent = 'Call in progress';
    waveform.classList.add('active');
    callTranscript.textContent = '';

    // Pick a random script and start typewriter
    const script = CALL_SCRIPTS[Math.floor(Math.random() * CALL_SCRIPTS.length)];
    typeCallScript(script);

    // Start timer
    state.callTimer = setInterval(() => {
      state.callSeconds++;
      callTimerEl.textContent = formatSeconds(state.callSeconds);
    }, 1000);

  }, 1500);
}

// ── endCall ───────────────────────────────────────────
async function endCall() {
  const durationSecs = state.callSeconds;

  cleanupCall(); // clears all timers & typewriter

  callStateLabel.textContent = 'Call ended';
  waveform.classList.remove('active');
  setCallBtn('start');

  // Stop audio recording and offer download
  const audioBlob = await stopAudioRecording();
  if (audioBlob && audioBlob.size > 1000) {
    downloadBlob(audioBlob, `ota-call-audio-${Date.now()}.webm`);
    showToast('✓ Call recording saved');
  }

  // Show download report button in call panel
  btnDownloadCall.classList.remove('hidden');
  // Also trigger the text report download
  exportCallReport(durationSecs);

  // Add to history
  addHistoryItem({
    id:      uid(),
    snippet: `Call · ${formatSeconds(durationSecs)}`,
    time:    nowTime(),
    type:    'call',
    status:  'resolved'
  });
  updateStats(true);

  // Reset UI labels after 2.5 s
  setTimeout(() => {
    callStateLabel.textContent = 'Ready to connect';
    callTimerEl.textContent    = '00:00';
  }, 2500);
}

// ── cleanupCall — clears ALL timers/intervals safely ──
function cleanupCall() {
  state.callActive = false;

  if (state.callStartTimeout) {
    clearTimeout(state.callStartTimeout);
    state.callStartTimeout = null;
  }
  if (state.callTimer) {
    clearInterval(state.callTimer);
    state.callTimer = null;
  }
  if (state.typewriterIv) {
    clearInterval(state.typewriterIv);
    state.typewriterIv = null;
  }

  callAvatarRing.classList.remove('ringing');
}

// ── Helper: swap call button icon/class ───────────────
function setCallBtn(mode) {
  if (mode === 'end') {
    btnCallToggle.classList.remove('call-start');
    btnCallToggle.classList.add('call-end');
    callIcon.innerHTML = `<path d="M4.293 4.293a1 1 0 011.414 0L10
      8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293
      4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1
      0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"/>`;
    btnCallToggle.setAttribute('aria-label', 'End call');
    btnCallToggle.title = 'End call';
  } else {
    btnCallToggle.classList.remove('call-end');
    btnCallToggle.classList.add('call-start');
    callIcon.innerHTML = `<path d="M2 3a1 1 0 011-1h2.153a1 1 0
      01.986.836l.74 4.435a1 1 0 01-.54 1.06l-1.548.773a11.037
      11.037 0 006.105 6.105l.774-1.548a1 1 0 011.059-.54l4.435.74a1
      1 0 01.836.986V17a1 1 0 01-1 1h-2C7.82 18 2 12.18 2 5V3z"/>`;
    btnCallToggle.setAttribute('aria-label', 'Start call');
    btnCallToggle.title = 'Start call';
  }
}

// Toggle
btnCallToggle.addEventListener('click', () => {
  if (!state.callActive) startCall();
  else endCall();
});

// Mute
btnMute.addEventListener('click', () => {
  state.muted = !state.muted;
  btnMute.classList.toggle('active', state.muted);
  btnMute.setAttribute('aria-label', state.muted ? 'Unmute microphone' : 'Mute microphone');
  btnMute.title = state.muted ? 'Unmute' : 'Mute';
  showToast(state.muted ? '🔇 Microphone muted' : '🎤 Microphone active');
});

// Speaker
btnSpeaker.addEventListener('click', () => {
  state.speakerOn = !state.speakerOn;
  btnSpeaker.classList.toggle('active', !state.speakerOn);
  btnSpeaker.setAttribute('aria-label', state.speakerOn ? 'Speaker on' : 'Speaker off');
  showToast(state.speakerOn ? '🔊 Speaker on' : '🔈 Speaker off');
});

// ══════════════════════════════════════════════════════
// HISTORY
// ══════════════════════════════════════════════════════
function addHistoryItem(item) {
  state.history.unshift(item);
  renderHistory();
}

function renderHistory() {
  if (historyEmpty) {
    historyEmpty.style.display = state.history.length ? 'none' : 'flex';
  }
  historyList.querySelectorAll('.history-item').forEach(n => n.remove());

  state.history.slice(0, 10).forEach(item => {
    const el = document.createElement('div');
    el.className = 'history-item';
    el.setAttribute('role', 'listitem');

    const iconSvg = item.type === 'call'
      ? `<svg viewBox="0 0 20 20" fill="currentColor" width="14" height="14"><path d="M2 3a1 1 0 011-1h2.153a1 1 0 01.986.836l.74 4.435a1 1 0 01-.54 1.06l-1.548.773a11.037 11.037 0 006.105 6.105l.774-1.548a1 1 0 011.059-.54l4.435.74a1 1 0 01.836.986V17a1 1 0 01-1 1h-2C7.82 18 2 12.18 2 5V3z"/></svg>`
      : `<svg viewBox="0 0 20 20" fill="currentColor" width="14" height="14"><path d="M2 5a2 2 0 012-2h12a2 2 0 012 2v8a2 2 0 01-2 2H6l-4 4V5z"/></svg>`;

    el.innerHTML = `
      <div class="history-icon">${iconSvg}</div>
      <div class="history-body">
        <div class="history-snippet">${item.snippet}</div>
        <div class="history-time">${item.time}</div>
      </div>
      <span class="history-badge badge-${item.status}">${item.status}</span>
    `;
    historyList.appendChild(el);
  });
}

btnClearHistory.addEventListener('click', () => {
  state.history  = [];
  state.chatLog  = [];
  state.sessions = 0;
  state.resolved = 0;
  renderHistory();
  statSessions.textContent = '0';
  statResolved.textContent = '0%';
  statRating.textContent   = '—';
  showToast('History cleared');
});

// ══════════════════════════════════════════════════════
// STATS
// ══════════════════════════════════════════════════════
function updateStats(resolved) {
  state.sessions++;
  if (resolved) state.resolved++;
  const pct = Math.round((state.resolved / state.sessions) * 100);
  statSessions.textContent = state.sessions;
  statResolved.textContent = pct + '%';
  statRating.textContent   = state.starRating > 0 ? state.starRating + '.0' : '—';
}

// ══════════════════════════════════════════════════════
// STARS / FEEDBACK
// ══════════════════════════════════════════════════════
starsRow.querySelectorAll('.star-btn').forEach(btn => {
  btn.addEventListener('mouseenter', () => highlightStars(+btn.dataset.val));
  btn.addEventListener('mouseleave', () => highlightStars(state.starRating));
  btn.addEventListener('click', () => {
    state.starRating = +btn.dataset.val;
    highlightStars(state.starRating);
    statRating.textContent = state.starRating + '.0';
  });
});

function highlightStars(n) {
  starsRow.querySelectorAll('.star-btn').forEach(b => {
    b.classList.toggle('active', +b.dataset.val <= n);
  });
}

btnSubmitFb.addEventListener('click', () => {
  const msg = feedbackText.value.trim();
  if (!state.starRating && !msg) {
    feedbackText.focus();
    showToast('Please select a rating or leave a comment.');
    return;
  }
  feedbackConfirm.classList.remove('hidden');
  feedbackText.value     = '';
  feedbackText.disabled  = true;
  btnSubmitFb.disabled   = true;
  btnSubmitFb.style.opacity = '0.5';
  showToast('✓ Feedback submitted — thank you!');

  setTimeout(() => {
    feedbackConfirm.classList.add('hidden');
    feedbackText.disabled = false;
    btnSubmitFb.disabled  = false;
    btnSubmitFb.style.opacity = '';
    state.starRating = 0;
    highlightStars(0);
  }, 3500);
});

// ══════════════════════════════════════════════════════
// SETTINGS (stub)
// ══════════════════════════════════════════════════════
$('btn-settings').addEventListener('click', () => {
  showToast('⚙ Settings panel coming soon');
});

// ══════════════════════════════════════════════════════
// INIT
// ══════════════════════════════════════════════════════
function init() {
  // Welcome message in chat — added to DOM but NOT to chatLog
  const row = document.createElement('div');
  row.className = 'bubble-row agent';

  const avatar = document.createElement('div');
  avatar.className = 'bubble-avatar';
  avatar.textContent = 'OA';

  const bubble = document.createElement('div');
  bubble.className = 'bubble';
  bubble.textContent = "Hello! I'm OTA Support, your AI assistant. How can I help you today?";

  const meta = document.createElement('div');
  meta.className = 'bubble-meta';
  meta.textContent = nowTime();

  const inner = document.createElement('div');
  inner.appendChild(bubble);
  inner.appendChild(meta);
  row.appendChild(avatar);
  row.appendChild(inner);
  chatMessages.appendChild(row);
}

init();
