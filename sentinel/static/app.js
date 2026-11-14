/* ==========================================================================
   CHRONOS // EDITORIAL MINIMALIST CLIENT CONTROLLER
   Aesthetic: Pure White, Off-Black (#111), Crisp Hairline Borders
   Typography: Satoshi Bold Everywhere | JetBrains Mono Data Floor
   ========================================================================== */

let state = {
  activeView: 'chat',
  chatHistory: [],
  channels: [],
  calendar: [],
  tasks: [],
  taskStats: { total: 0, done: 0, in_progress: 0, pending: 0, critical: 0, high: 0 },
  mcps: [],
  agentTools: [],
  toolDiagnostics: {},
  models: [],
  activeModel: 'qwen2.5:3b',
  activeProvider: 'ollama',
  briefing: null,
  activeEvent: null,
  targetDeadline: null,
  isProcessing: false,
  timelineFilter: 'all',
  activeToolTab: 'catalog'
};

let heroDeckTemplate = null;

document.addEventListener("DOMContentLoaded", () => {
  initApp();
});

async function initApp() {
  // Cache hero deck template for reset
  const hero = document.getElementById("hero-command-deck");
  if (hero) heroDeckTemplate = hero.cloneNode(true);

  startLiveClock();
  startRadarCountdown();
  await loadModels();
  await loadChatHistory();
  await loadBriefing();
  await loadEventsAndRadar();
  await loadCalendar();
  await loadAndRenderTaskConsole();
  await loadMcps();
  await loadAndRenderAgentTools();
  await loadChannels();

  // Periodic background check
  setInterval(loadBriefing, 15000);
  setInterval(checkModelStatus, 10000);
}

// ── Direct In-App Notifications & Modal System (No Browser Alerts) ───────

function showToast(message, type = 'info', duration = 3800) {
  const container = document.getElementById("toast-container");
  if (!container) return;

  const toast = document.createElement("div");
  toast.className = `chronos-toast toast-${type}`;
  
  let iconSvg = '';
  if (type === 'success') {
    iconSvg = '<svg class="size-4 text-emerald-400 shrink-0 mt-0.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"></polyline></svg>';
  } else if (type === 'error') {
    iconSvg = '<svg class="size-4 text-red-400 shrink-0 mt-0.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>';
  } else if (type === 'warning') {
    iconSvg = '<svg class="size-4 text-amber-400 shrink-0 mt-0.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>';
  } else {
    iconSvg = '<svg class="size-4 text-zinc-300 shrink-0 mt-0.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>';
  }

  toast.innerHTML = `
    ${iconSvg}
    <div class="flex-1 text-[13px] font-bold leading-snug">${escapeHtml(message)}</div>
    <button class="text-zinc-400 hover:text-white cursor-pointer ml-1 text-sm font-bold">&times;</button>
  `;

  toast.querySelector("button").onclick = () => {
    toast.style.opacity = '0';
    setTimeout(() => toast.remove(), 200);
  };

  container.appendChild(toast);

  setTimeout(() => {
    if (toast.parentNode) {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(8px)';
      setTimeout(() => toast.remove(), 250);
    }
  }, duration);
}

function showConfirmModal(title, message, confirmBtnText = "Confirm", onConfirm) {
  const modal = document.getElementById("confirm-modal");
  const titleEl = document.getElementById("confirm-modal-title");
  const msgEl = document.getElementById("confirm-modal-message");
  const cancelBtn = document.getElementById("confirm-modal-cancel");
  const submitBtn = document.getElementById("confirm-modal-submit");

  if (!modal) {
    if (onConfirm) onConfirm();
    return;
  }

  titleEl.textContent = title;
  msgEl.textContent = message;
  submitBtn.textContent = confirmBtnText;

  modal.classList.remove("hidden");

  const cleanup = () => {
    modal.classList.add("hidden");
    cancelBtn.onclick = null;
    submitBtn.onclick = null;
  };

  cancelBtn.onclick = () => cleanup();
  submitBtn.onclick = () => {
    cleanup();
    if (onConfirm) onConfirm();
  };
}

// ── Clock & Countdown Engines ──────────────────────────────────────────

function startLiveClock() {
  const clockEl = document.getElementById("live-clock");
  if (!clockEl) return;
  const update = () => {
    const d = new Date();
    clockEl.textContent = d.toTimeString().split(' ')[0];
  };
  update();
  setInterval(update, 1000);
}

function startRadarCountdown() {
  const cdEl = document.getElementById("radar-countdown");
  const timelineCdEl = document.getElementById("timeline-countdown-display");
  setInterval(() => {
    let text = "--:--:--";
    if (!state.targetDeadline) {
      text = "--:--:--";
    } else {
      const now = new Date();
      const diff = state.targetDeadline - now;
      if (diff <= 0) {
        text = "DEADLINE REACHED";
      } else {
        const days = Math.floor(diff / (1000 * 60 * 60 * 24));
        const hours = Math.floor((diff / (1000 * 60 * 60)) % 24);
        const mins = Math.floor((diff / (1000 * 60)) % 60);
        const secs = Math.floor((diff / 1000) % 60);
        if (days > 0) {
          text = `${days}d ${String(hours).padStart(2, '0')}h ${String(mins).padStart(2, '0')}m`;
        } else {
          text = `${String(hours).padStart(2, '0')}:${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
        }
      }
    }
    if (cdEl) cdEl.textContent = text;
    if (timelineCdEl) timelineCdEl.textContent = text;
  }, 1000);
}

// ── Models & Provider Switcher ─────────────────────────────────────────

async function loadModels() {
  try {
    const res = await fetch("/api/models");
    const models = await res.json();
    state.models = models;

    const activeRes = await fetch("/api/models/active");
    const activeData = await activeRes.json();
    state.activeModel = activeData.model || 'qwen2.5:3b';
    state.activeProvider = activeData.provider || 'ollama';

    renderModelSelector();
    checkModelStatus();
  } catch (err) {
    console.warn("Could not load models list:", err);
  }
}

function renderModelSelector() {
  const selector = document.getElementById("model-selector");
  if (!selector) return;

  const ollamaModels = state.models.filter(m => m.provider === 'ollama');
  const groqModels = state.models.filter(m => m.provider === 'groq');

  let html = '';
  if (ollamaModels.length > 0) {
    html += '<optgroup label="Local (Ollama)">';
    ollamaModels.forEach(m => {
      const selected = m.id === state.activeModel ? 'selected' : '';
      html += `<option value="${escapeHtml(m.id)}" data-provider="ollama" ${selected}>${escapeHtml(m.name)} [Local]</option>`;
    });
    html += '</optgroup>';
  }

  if (groqModels.length > 0) {
    html += '<optgroup label="Cloud (Groq LPU)">';
    groqModels.forEach(m => {
      const selected = m.id === state.activeModel ? 'selected' : '';
      html += `<option value="${escapeHtml(m.id)}" data-provider="groq" ${selected}>${escapeHtml(m.name)} [Groq]</option>`;
    });
    html += '</optgroup>';
  }

  if (!html) {
    html = `<option value="${escapeHtml(state.activeModel)}" selected>${escapeHtml(state.activeModel)}</option>`;
  }

  selector.innerHTML = html;
}

async function switchModel(modelId) {
  const selectedObj = state.models.find(m => m.id === modelId);
  const provider = selectedObj ? selectedObj.provider : (modelId.includes('/') ? 'groq' : 'ollama');

  state.activeModel = modelId;
  state.activeProvider = provider;

  updateModelActivity('idle', `Switched to ${modelId}`);

  try {
    const res = await fetch("/api/models/switch", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ model: modelId, provider: provider })
    });
    const data = await res.json();
    checkModelStatus();
    showToast(`Switched active intelligence to ${modelId}`, "success", 2000);
  } catch (err) {
    showToast("Failed to switch model: " + err, "error");
  }
}

async function checkModelStatus() {
  const dot = document.getElementById("model-status-dot");
  try {
    const res = await fetch("/api/models/status");
    const data = await res.json();
    if (dot) {
      dot.className = data.status === "online" 
        ? "size-1.5 rounded-full bg-emerald-500" 
        : "size-1.5 rounded-full bg-amber-500";
    }
  } catch (err) {
    if (dot) dot.className = "size-1.5 rounded-full bg-zinc-400";
  }
}

// ── Sidebar Model Activity Monitor ─────────────────────────────────────

function updateModelActivity(mode, label) {
  const fill = document.getElementById("model-activity-fill");
  const text = document.getElementById("model-activity-text");

  if (!fill || !text) return;

  if (mode === 'thinking') {
    fill.style.width = '100%';
    fill.className = 'h-full activity-active';
    text.textContent = label || `Reasoning with ${state.activeModel}...`;
    text.className = 'text-[13px] font-mono text-[#111] font-semibold';
  } else if (mode === 'streaming') {
    fill.style.width = '100%';
    fill.className = 'h-full bg-[#111] transition-all duration-150';
    text.textContent = label || 'Streaming response...';
    text.className = 'text-[13px] font-mono text-[#111] font-semibold';
  } else {
    fill.style.width = '0%';
    fill.className = 'h-full bg-zinc-300 transition-all duration-300';
    text.textContent = label || 'Model idle';
    text.className = 'text-[13px] font-mono text-zinc-400';
  }
}

// ── View Switcher ──────────────────────────────────────────────────────

function switchView(viewName) {
  state.activeView = viewName;

  document.querySelectorAll(".view-panel").forEach(p => p.classList.add("hidden"));
  const target = document.getElementById(`view-${viewName}`);
  if (target) target.classList.remove("hidden");

  ['chat', 'matrix', 'tasks', 'mcps', 'connectors', 'channels'].forEach(v => {
    const btn = document.getElementById(`nav-${v}`);
    if (btn) {
      if (v === viewName) {
        btn.className = "nav-btn nav-btn-active";
      } else {
        btn.className = "nav-btn text-zinc-600 hover:bg-zinc-50 hover:text-[#111]";
      }
    }
  });

  if (viewName === 'matrix') renderFullCalendar();
  if (viewName === 'tasks') loadAndRenderTaskConsole();
  if (viewName === 'mcps') {
    loadAndRenderAgentTools();
    renderFullMcps();
  }
  if (viewName === 'connectors') loadAndRenderConnectors();
  if (viewName === 'channels') renderFullChannels();
  if (viewName === 'chat') scrollToBottom();
}

function toggleSidebar() {
  const sb = document.getElementById("sidebar");
  if (sb) sb.classList.toggle("hidden");
}

// ── Events, Radar & Briefing ───────────────────────────────────────────

async function loadEventsAndRadar() {
  try {
    const res = await fetch("/api/events");
    const events = await res.json();
    if (events.length > 0) {
      state.activeEvent = events[0];
      const rawDate = events[0].deadline || "";
      const cleaned = rawDate.replace("Z", "").replace(" ", "T");
      state.targetDeadline = cleaned ? new Date(cleaned) : null;
      const titleEl = document.getElementById("radar-event-title");
      if (titleEl) titleEl.textContent = events[0].title;
    }
    updateRadarProgress();
  } catch (err) {
    console.error("Failed to load events:", err);
  }
}

function updateRadarProgress() {
  const tasks = state.calendar.filter(i => i.type === 'milestone_task' || i.type === 'task_due');
  const countEl = document.getElementById("sidebar-task-count");
  if (countEl) countEl.textContent = tasks.length;

  if (tasks.length === 0) {
    setRadarProgress(0);
    return;
  }
  const completed = tasks.filter(t => t.status === 'done').length;
  const pct = Math.round((completed / tasks.length) * 100);
  setRadarProgress(pct);
}

function setRadarProgress(pct) {
  const bar = document.getElementById("radar-progress-bar");
  const text = document.getElementById("radar-progress-pct");
  if (bar) bar.style.width = `${pct}%`;
  if (text) text.textContent = `${pct}%`;
}

async function loadBriefing() {
  try {
    const res = await fetch("/api/briefing");
    const data = await res.json();
    state.briefing = data;
  } catch (err) {
    console.error("Failed to load briefing:", err);
  }
}

// ── Chat Engine with 100% Reliable In-Place Response Rendering ─────────

async function loadChatHistory() {
  try {
    const res = await fetch("/api/chat/history");
    const history = await res.json();
    state.chatHistory = history;
    renderChat();
  } catch (err) {
    console.error("Failed to load chat history:", err);
  }
}

function renderChat() {
  const container = document.getElementById("chat-history");
  if (!container) return;

  if (!state.chatHistory || state.chatHistory.length === 0) {
    container.innerHTML = "";
    if (heroDeckTemplate) {
      const clone = heroDeckTemplate.cloneNode(true);
      clone.classList.remove("hidden");
      container.appendChild(clone);
    }
    return;
  }

  let html = state.chatHistory.map(msg => renderMessageHtml(msg)).join("");
  container.innerHTML = html;
  scrollToBottom();
}

function renderMessageHtml(msg) {
  const isUser = msg.role === "user";
  const formattedContent = formatMarkdown(msg.content);

  if (isUser) {
    return `
      <div class="flex justify-end animate-fadeIn my-6">
        <div class="max-w-xl rounded-xl rounded-tr-xs bg-[#111] text-white px-5 py-3.5 text-[15px] font-bold leading-relaxed shadow-sm">
          ${formattedContent}
        </div>
      </div>
    `;
  }

  let cardHtml = "";
  if (msg.card_type === "research_brief" && msg.metadata) {
    cardHtml = renderResearchCard(msg.metadata);
  } else if (msg.card_type === "tasks_and_mcps" && msg.metadata) {
    cardHtml = renderTasksAndMcpsCard(msg.metadata);
  } else if (msg.card_type === "briefing_card" && msg.metadata) {
    cardHtml = renderBriefingCard(msg.metadata);
  } else if (msg.card_type === "channel_connect_trigger") {
    cardHtml = `
      <div class="pt-2">
        <button onclick="switchView('channels')" class="inline-flex items-center gap-2 h-10 px-4 rounded-lg bg-[#111] text-white text-[14px] font-semibold hover:bg-zinc-800 transition-colors cursor-pointer">
          <span>Configure Channels</span>
        </button>
      </div>
    `;
  }

  return `
    <div class="flex items-start gap-4 max-w-3xl animate-fadeIn my-6 group">
      <div class="size-8 rounded-lg bg-[#111] flex items-center justify-center text-white shrink-0 mt-0.5">
        <svg class="size-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="10"></circle>
          <polyline points="12 6 12 12 16 14"></polyline>
        </svg>
      </div>
      <div class="flex-1 space-y-3">
        <div class="text-[15px] text-[#111] leading-relaxed message-content">
          ${formattedContent}
        </div>
        ${cardHtml}
        <div class="flex items-center gap-2 pt-1 text-[11px] font-mono text-zinc-400">
          <span class="font-extrabold text-zinc-600">CHRONOS SENTINEL</span>
          <span>·</span>
          <button onclick="copyMessageText(this)" class="hover:text-[#111] underline cursor-pointer font-bold transition-colors">Copy</button>
        </div>
      </div>
    </div>
  `;
}

function renderResearchCard(meta) {
  return `
    <div class="rounded-xl border border-[#e4e4e7] bg-white p-5 space-y-4">
      <div class="flex items-center justify-between border-b border-zinc-100 pb-3">
        <div class="text-[13px] font-mono font-bold uppercase tracking-wider text-[#111]">
          Pre-Research // ${escapeHtml(meta.event_title || '')}
        </div>
        <span class="px-2 py-0.5 rounded text-[12px] font-mono font-semibold bg-zinc-100 text-[#111]">
          Verified
        </span>
      </div>

      <p class="text-[14px] text-zinc-600 leading-relaxed font-bold">
        ${escapeHtml(meta.summary || '')}
      </p>

      <div class="space-y-2 pt-1">
        <div class="text-[12px] font-mono uppercase text-zinc-400 font-semibold">Priority Tracks:</div>
        <div class="flex flex-wrap gap-2">
          <button onclick="quickSend('I want to prioritize Track 1 with Python backend and solo builder mode')" class="h-9 px-3.5 rounded-lg border border-[#e4e4e7] bg-zinc-50 hover:bg-[#111] hover:text-white text-[13px] font-bold text-[#111] transition-all cursor-pointer">
            Track 1: Autonomous Agent (Python)
          </button>
          <button onclick="quickSend('Solo builder mode with full-stack UI, Chrome DevTools testing')" class="h-9 px-3.5 rounded-lg border border-[#e4e4e7] bg-zinc-50 hover:bg-[#111] hover:text-white text-[13px] font-bold text-[#111] transition-all cursor-pointer">
            Solo Builder (Full-Stack UI)
          </button>
        </div>
      </div>
    </div>
  `;
}

function renderTasksAndMcpsCard(meta) {
  const tasks = meta.tasks || [];
  const mcps = meta.mcps || [];

  const tasksHtml = tasks.map(t => `
    <div class="flex items-start gap-3 p-3.5 rounded-lg border border-[#e4e4e7] bg-zinc-50/50 ${t.status === 'done' ? 'opacity-50 line-through' : ''}">
      <input type="checkbox" class="accent-[#111] size-4 rounded mt-1 cursor-pointer" ${t.status === 'done' ? 'checked' : ''} onchange="toggleTaskInChat(${t.id}, this.checked)">
      <div class="flex-1 space-y-1">
        <div class="text-[14px] font-bold text-[#111]">${escapeHtml(t.title)}</div>
        <div class="flex items-center gap-2 text-[12px] font-mono text-zinc-500 font-semibold">
          <span class="px-1.5 py-0.5 rounded bg-zinc-200 text-zinc-800">${t.phase}</span>
          <span>Due: ${t.due_date || 'TBD'}</span>
          ${t.assigned_mcp ? `<span class="px-1.5 py-0.5 rounded bg-zinc-100 text-zinc-700">Tool: ${escapeHtml(t.assigned_mcp)}</span>` : ''}
        </div>
      </div>
    </div>
  `).join("");

  const mcpsHtml = mcps.slice(0, 3).map(m => `
    <div class="flex items-center justify-between p-3 rounded-lg border border-[#e4e4e7] bg-white font-mono text-[13px]">
      <span class="font-bold text-[#111]">${escapeHtml(m.name)}</span>
      <div class="flex items-center gap-2">
        <code class="px-2 py-0.5 rounded bg-zinc-100 text-zinc-800">${escapeHtml(m.install_command)}</code>
        <button onclick="copyToClipboard('${escapeHtml(m.install_command)}', this)" class="px-2 py-0.5 rounded bg-zinc-200 hover:bg-[#111] hover:text-white text-[12px] font-semibold transition-colors cursor-pointer">Copy</button>
      </div>
    </div>
  `).join("");

  return `
    <div class="rounded-xl border border-[#e4e4e7] bg-white p-5 space-y-4">
      <div class="flex items-center justify-between border-b border-zinc-100 pb-3">
        <div class="text-[13px] font-mono font-bold uppercase tracking-wider text-[#111]">
          Phased Milestones &amp; MCP Stack
        </div>
        <button onclick="switchView('matrix')" class="text-[13px] font-semibold text-zinc-600 hover:text-[#111] cursor-pointer">
          Timeline &rarr;
        </button>
      </div>

      <div class="space-y-2">
        ${tasksHtml}
      </div>

      <div class="space-y-2 pt-2 border-t border-zinc-100">
        <div class="text-[12px] font-mono uppercase text-zinc-400 font-semibold">Configured Tools:</div>
        <div class="space-y-2">
          ${mcpsHtml}
        </div>
      </div>

      <div class="flex items-center gap-2 pt-1">
        <button onclick="exportMcpConfig()" class="h-9 px-4 rounded-lg bg-[#111] text-white text-[13px] font-semibold hover:bg-zinc-800 transition-all cursor-pointer">
          Export Config
        </button>
        <button onclick="switchView('channels')" class="h-9 px-4 rounded-lg border border-[#e4e4e7] hover:bg-zinc-50 text-[13px] font-semibold text-zinc-700 transition-all cursor-pointer">
          Connect Alerts
        </button>
      </div>
    </div>
  `;
}

function renderBriefingCard(meta) {
  const briefing = meta.briefing || {};
  return `
    <div class="rounded-xl border-l-4 border-l-[#111] border border-[#e4e4e7] bg-white p-5 space-y-2">
      <div class="text-[12px] font-mono uppercase text-zinc-500 font-bold">
        ${escapeHtml(briefing.header || 'EXECUTIVE BRIEFING')}
      </div>
      <div class="text-[14px] font-bold text-[#111] leading-snug">
        ${escapeHtml(briefing.message || '')}
      </div>
      <button onclick="switchView('matrix')" class="text-[13px] font-semibold text-zinc-600 hover:text-[#111] underline pt-1 cursor-pointer">
        Inspect Schedule Timeline
      </button>
    </div>
  `;
}

// ── Sending Messages (Instant Visible Feedback, Zero Refresh Needed) ──

function copyMessageText(btn) {
  const bubble = btn.closest(".group");
  const contentEl = bubble ? bubble.querySelector(".message-content") : null;
  const text = contentEl ? contentEl.innerText.trim() : "";
  if (!text) return;

  navigator.clipboard.writeText(text).then(() => {
    const orig = btn.textContent;
    btn.textContent = "Copied!";
    showToast("Message copied to clipboard", "info", 1500);
    setTimeout(() => { btn.textContent = orig; }, 1800);
  });
}

async function handleSend(e) {
  if (e) e.preventDefault();
  if (state.isProcessing) return;

  const input = document.getElementById("chat-input");
  const text = input ? input.value.trim() : "";
  if (!text) return;

  if (input) input.value = "";
  state.isProcessing = true;

  const container = document.getElementById("chat-history");

  // Remove hero command deck if it is currently displayed
  const hero = document.getElementById("hero-command-deck");
  if (hero) hero.remove();

  // Optimistic User Bubble - Direct DOM append
  const userMsg = {
    role: "user",
    content: text,
    card_type: null,
    metadata: {}
  };
  state.chatHistory.push(userMsg);

  const userWrap = document.createElement("div");
  userWrap.innerHTML = renderMessageHtml(userMsg);
  if (container) {
    container.appendChild(userWrap.firstElementChild);
    scrollToBottom();
  }

  // Sidebar Thinking Animation
  const startTime = Date.now();
  updateModelActivity('thinking', `Reasoning with ${state.activeModel}...`);

  // Direct DOM Insert for In-Chat Thinking Indicator
  const thinkingRow = document.createElement("div");
  thinkingRow.id = "thinking-bubble";
  thinkingRow.className = "flex items-start gap-4 max-w-3xl animate-fadeIn my-6";
  thinkingRow.innerHTML = `
    <div class="size-8 rounded-lg bg-[#111] flex items-center justify-center text-white shrink-0 mt-0.5">
      <svg class="size-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
        <circle cx="12" cy="12" r="10"></circle>
        <polyline points="12 6 12 12 16 14"></polyline>
      </svg>
    </div>
    <div class="flex-1 space-y-2">
      <div class="text-[15px] text-[#111] leading-relaxed message-content">
        <span class="thinking-wave">
          <span class="thinking-dot"></span>
          <span class="thinking-dot"></span>
          <span class="thinking-dot"></span>
        </span>
        <span class="ml-2 text-[13px] font-mono text-zinc-400 font-semibold">Thinking with ${escapeHtml(state.activeModel)}...</span>
      </div>
    </div>
  `;
  if (container) {
    container.appendChild(thinkingRow);
    scrollToBottom();
  }

  // Primary Reliable Chat Request
  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text })
    });

    if (!res.ok) {
      throw new Error(`HTTP ${res.status}: ${res.statusText}`);
    }

    const data = await res.json();
    const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);

    // Remove thinking bubble immediately
    const tb = document.getElementById("thinking-bubble");
    if (tb) tb.remove();

    // Push assistant reply into state
    state.chatHistory.push(data);

    // Direct DOM append for Assistant Message
    const assistantWrap = document.createElement("div");
    assistantWrap.innerHTML = renderMessageHtml(data);
    if (container) {
      container.appendChild(assistantWrap.firstElementChild);
      scrollToBottom();
    }

    updateModelActivity('idle', `Response in ${elapsed}s`);

    // Background sync
    loadBriefing();
    loadEventsAndRadar();
    loadCalendar();
    loadMcps();

    if (data.card_type === "research_brief") {
      showToast("Event links digested and research dossier synthesized.", "success");
    } else if (data.card_type === "tasks_and_mcps") {
      showToast("Phased milestones and MCP stack configured.", "success");
    }

  } catch (err) {
    const tb = document.getElementById("thinking-bubble");
    if (tb) tb.remove();
    updateModelActivity('idle', 'Model idle');
    showToast("Error communicating with CHRONOS engine: " + err.message, "error");
    console.error("Chat error:", err);
  } finally {
    state.isProcessing = false;
  }
}

function quickSend(text) {
  if (state.activeView !== 'chat') switchView('chat');
  const input = document.getElementById("chat-input");
  if (input) {
    input.value = text;
    handleSend();
  }
}

async function toggleTaskInChat(taskId, isDone) {
  const status = isDone ? "done" : "pending";
  try {
    await fetch(`/api/tasks/${taskId}/status`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status })
    });
    await loadCalendar();
    updateRadarProgress();
    loadBriefing();
    showToast(`Task marked as ${status}`, "info", 1500);
  } catch (err) {
    showToast("Failed to update task: " + err, "error");
  }
}

function resetChat() {
  showConfirmModal(
    "Reset Conversation",
    "Are you sure you want to clear your conversation history? Your events and scheduled milestones will remain saved.",
    "Clear History",
    async () => {
      try {
        await fetch("/api/chat/reset", { method: "POST" });
        state.chatHistory = [];
        renderChat();
        showToast("Conversation cleared", "info", 2000);
      } catch (e) {
        showToast("Reset failed: " + e, "error");
      }
    }
  );
}

function scrollToBottom() {
  const container = document.getElementById("chat-history");
  if (container) container.scrollTop = container.scrollHeight;
}

// ── Timeline Calendar View ─────────────────────────────────────────────

async function loadCalendar() {
  try {
    const res = await fetch("/api/calendar");
    state.calendar = await res.json();
    updateRadarProgress();
    if (state.activeView === 'matrix') renderFullCalendar();
  } catch (err) {
    console.error("Failed to load calendar:", err);
  }
}

function setTimelineFilter(filter) {
  state.timelineFilter = filter;
  ['all', 'pending', 'done', 'deadlines'].forEach(f => {
    const btn = document.getElementById(`filter-${f}`);
    if (btn) {
      if (f === filter) {
        btn.className = "filter-btn filter-btn-active";
      } else {
        btn.className = "filter-btn";
      }
    }
  });
  renderFullCalendar();
}

function toggleAddTaskForm() {
  const form = document.getElementById("timeline-add-form");
  if (form) form.classList.toggle("hidden");
}

async function handleCreateCustomTask(e) {
  if (e) e.preventDefault();
  const eventId = state.activeEvent ? state.activeEvent.id : 1;
  const title = document.getElementById("new-task-title")?.value?.trim();
  const phase = document.getElementById("new-task-phase")?.value || "Phase 1: Setup";
  const dueDate = document.getElementById("new-task-due")?.value?.trim() || "";
  const assignedMcp = document.getElementById("new-task-mcp")?.value?.trim() || "";
  const priority = document.getElementById("new-task-priority")?.value || "high";

  if (!title) return;

  try {
    await fetch("/api/tasks", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        event_id: eventId,
        title,
        phase,
        due_date: dueDate,
        assigned_mcp: assignedMcp,
        priority
      })
    });

    document.getElementById("new-task-title").value = "";
    document.getElementById("new-task-due").value = "";
    document.getElementById("new-task-mcp").value = "";
    toggleAddTaskForm();

    await loadCalendar();
    await loadEventsAndRadar();
    renderFullCalendar();
    showToast("New milestone added to timeline", "success");
  } catch (err) {
    showToast("Failed to create task: " + err, "error");
  }
}

function deleteTaskInTimeline(taskId) {
  showConfirmModal(
    "Delete Milestone",
    "Are you sure you want to delete this scheduled milestone?",
    "Delete",
    async () => {
      try {
        await fetch(`/api/tasks/${taskId}`, { method: "DELETE" });
        await loadCalendar();
        await loadEventsAndRadar();
        renderFullCalendar();
        showToast("Milestone removed", "info");
      } catch (err) {
        showToast("Delete failed: " + err, "error");
      }
    }
  );
}

function formatRelativeTime(dateStr) {
  if (!dateStr) return "";
  try {
    const target = new Date(dateStr.replace(" ", "T"));
    const now = new Date();
    const diffMs = target - now;
    const diffHours = Math.round(diffMs / (1000 * 60 * 60));

    if (diffMs < 0) {
      const pastHours = Math.abs(diffHours);
      if (pastHours < 24) return `${pastHours}h overdue`;
      return `${Math.round(pastHours / 24)}d overdue`;
    }
    if (diffHours < 1) return `Due in < 1 hour`;
    if (diffHours < 24) return `Due in ${diffHours} hours`;
    const days = Math.round(diffHours / 24);
    return `Due in ${days} days`;
  } catch (e) {
    return "";
  }
}

function renderFullCalendar() {
  const container = document.getElementById("full-calendar-list");
  if (!container) return;

  const tasks = state.calendar.filter(i => i.type === 'task_due');
  const completed = tasks.filter(t => t.status === 'done').length;
  const pct = tasks.length > 0 ? Math.round((completed / tasks.length) * 100) : 0;

  const totalBadge = document.getElementById("timeline-total-badge");
  if (totalBadge) totalBadge.textContent = `${tasks.length} Milestones`;

  const countdownDisp = document.getElementById("timeline-countdown-display");
  const radarCountdown = document.getElementById("radar-countdown");
  if (countdownDisp && radarCountdown) {
    countdownDisp.textContent = radarCountdown.textContent;
  }

  const eventNameDisp = document.getElementById("timeline-event-name");
  if (eventNameDisp && state.activeEvent) {
    eventNameDisp.textContent = state.activeEvent.title;
  }

  const ratioDisp = document.getElementById("timeline-progress-ratio");
  const barFill = document.getElementById("timeline-bar-fill");
  const detailDisp = document.getElementById("timeline-progress-detail");
  if (ratioDisp) ratioDisp.textContent = `${pct}%`;
  if (barFill) barFill.style.width = `${pct}%`;
  if (detailDisp) detailDisp.textContent = `${completed} of ${tasks.length} milestones cleared`;

  const toolCountDisp = document.getElementById("timeline-tool-count");
  if (toolCountDisp) toolCountDisp.textContent = `${state.mcps.length} Tools Mapped`;

  let filtered = state.calendar;
  if (state.timelineFilter === 'pending') {
    filtered = state.calendar.filter(i => i.type === 'task_due' && i.status !== 'done');
  } else if (state.timelineFilter === 'done') {
    filtered = state.calendar.filter(i => i.type === 'task_due' && i.status === 'done');
  } else if (state.timelineFilter === 'deadlines') {
    filtered = state.calendar.filter(i => i.type === 'event_deadline');
  }

  if (filtered.length === 0) {
    container.innerHTML = `
      <div class="text-[14px] text-zinc-500 p-8 bg-zinc-50 rounded-xl border border-[#e4e4e7] space-y-2">
        <div class="text-[15px] font-bold text-[#111]">No milestones match the current filter.</div>
        <div class="text-zinc-400">Switch filter tabs above or click "+ Add Milestone" to schedule a task.</div>
      </div>
    `;
    return;
  }

  let stepNumber = 0;
  container.innerHTML = filtered.map(item => {
    const isDeadline = item.type === 'event_deadline';

    if (isDeadline) {
      return `
        <div class="relative pl-10 my-8">
          <div class="timeline-item-node deadline">
            <svg class="size-3.5 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
              <circle cx="12" cy="12" r="10"></circle>
              <polyline points="12 6 12 12 16 14"></polyline>
            </svg>
          </div>
          <div class="p-6 rounded-xl border-2 border-[#111] bg-white space-y-3 shadow-md">
            <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-zinc-100 pb-3">
              <div class="flex items-center gap-2">
                <span class="px-2.5 py-1 rounded-md text-[12px] font-mono font-extrabold bg-[#111] text-white tracking-wider">
                  FINAL TARGET DEADLINE
                </span>
                <span class="text-[13px] font-mono font-bold text-zinc-500">
                  Buffer Lock Active
                </span>
              </div>
              <div class="text-[14px] font-mono font-extrabold text-[#111]">
                ${escapeHtml(item.date)}
              </div>
            </div>

            <div class="text-lg font-extrabold text-[#111] leading-tight">
              ${escapeHtml(item.title)}
            </div>

            ${item.description ? `
              <p class="text-[14px] text-zinc-600 leading-relaxed font-bold">
                ${escapeHtml(item.description)}
              </p>
            ` : ''}

            <div class="flex flex-wrap items-center gap-3 pt-2 text-[13px] font-mono font-bold text-zinc-500">
              <span class="inline-flex items-center gap-1.5 text-emerald-600">
                <span class="size-2 rounded-full bg-emerald-500 animate-pulse"></span>
                <span>Automated SAR &amp; Portal Lock Freeze</span>
              </span>
              <span>·</span>
              <span>Local Daemon Monitoring 24/7</span>
            </div>
          </div>
        </div>
      `;
    }

    stepNumber += 1;
    const isDone = item.status === 'done';
    const relativeTime = formatRelativeTime(item.date);

    let phaseBadgeClass = "bg-zinc-100 text-[#111]";
    if (item.phase && item.phase.includes("Phase 2")) phaseBadgeClass = "bg-[#111] text-white";
    if (item.phase && item.phase.includes("Phase 4")) phaseBadgeClass = "bg-emerald-100 text-emerald-900 border border-emerald-300";

    return `
      <div class="relative pl-10 my-4 group">
        <div class="timeline-item-node ${isDone ? 'completed' : 'pending-active'}">
          ${isDone ? `
            <svg class="size-3.5 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
              <polyline points="20 6 9 17 4 12"></polyline>
            </svg>
          ` : `
            <span class="text-[11px] font-mono font-bold text-[#111]">${stepNumber}</span>
          `}
        </div>

        <div class="p-5 rounded-xl border border-[#e4e4e7] ${isDone ? 'bg-zinc-50/70 border-zinc-200 opacity-60' : 'bg-white hover:border-zinc-400 hover:shadow-subtle'} transition-all space-y-3 shadow-2xs">
          
          <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div class="flex items-center gap-2">
              <span class="px-2 py-0.5 rounded text-[12px] font-mono font-bold ${phaseBadgeClass}">
                ${escapeHtml(item.phase || 'Phase Milestone')}
              </span>
              ${item.priority ? `
                <span class="px-2 py-0.5 rounded text-[11px] font-mono font-extrabold uppercase ${item.priority === 'critical' ? 'bg-red-100 text-red-900 border border-red-200' : 'bg-zinc-100 text-zinc-700'}">
                  ${item.priority}
                </span>
              ` : ''}
            </div>

            <div class="flex items-center gap-2 text-[13px] font-mono">
              ${relativeTime ? `
                <span class="px-2 py-0.5 rounded-full text-[11px] font-bold ${relativeTime.includes('overdue') ? 'bg-red-100 text-red-700' : 'bg-zinc-100 text-zinc-600'}">
                  ${relativeTime}
                </span>
              ` : ''}
              <span class="text-zinc-500 font-semibold">${item.date || 'TBD'}</span>
            </div>
          </div>

          <div class="flex items-start gap-3">
            <input 
              type="checkbox" 
              class="accent-[#111] size-5 rounded-md mt-0.5 cursor-pointer shrink-0" 
              ${isDone ? 'checked' : ''} 
              onchange="toggleTaskInTimeline(${item.task_id || 0}, this.checked)"
              title="Mark milestone complete"
            />
            <div class="flex-1 space-y-1">
              <div class="text-[15px] font-extrabold text-[#111] ${isDone ? 'line-through text-zinc-400' : ''}">
                ${escapeHtml(item.title)}
              </div>
              ${item.description ? `
                <p class="text-[13px] text-zinc-500 leading-relaxed font-bold">
                  ${escapeHtml(item.description)}
                </p>
              ` : ''}
            </div>
          </div>

          <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pt-2 border-t border-zinc-100 text-[13px]">
            <div class="flex items-center gap-2">
              ${item.assigned_mcp ? `
                <div class="flex items-center gap-1.5 font-mono text-[12px] text-zinc-600 font-bold">
                  <svg class="size-3.5 text-zinc-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="16 18 22 12 16 6"></polyline><polyline points="8 6 2 12 8 18"></polyline></svg>
                  <span>Tool:</span>
                  <code class="px-1.5 py-0.5 rounded bg-zinc-100 text-[#111] border border-zinc-200">${escapeHtml(item.assigned_mcp)}</code>
                </div>
              ` : `
                <span class="text-zinc-400 font-mono text-[12px]">No tool assigned</span>
              `}
            </div>

            <div class="flex items-center gap-2 shrink-0">
              ${item.task_id ? `
                <button onclick="deleteTaskInTimeline(${item.task_id})" class="text-[12px] font-mono text-zinc-400 hover:text-red-600 cursor-pointer transition-colors" title="Delete milestone">
                  Delete
                </button>
              ` : ''}
            </div>
          </div>

        </div>
      </div>
    `;
  }).join("");
}

async function toggleTaskInTimeline(taskId, isDone) {
  if (!taskId) return;
  const status = isDone ? "done" : "pending";
  try {
    await fetch(`/api/tasks/${taskId}/status`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status })
    });
    await loadCalendar();
    updateRadarProgress();
    loadBriefing();
    renderFullCalendar();
    showToast(`Milestone marked as ${status}`, "info", 1500);
  } catch (err) {
    showToast("Failed to update status: " + err, "error");
  }
}

// ── Dedicated Task Management Console ──────────────────────────────────

async function loadAndRenderTaskConsole() {
  try {
    const [tasksRes, statsRes] = await Promise.all([
      fetch("/api/tasks"),
      fetch("/api/tasks/stats")
    ]);
    state.tasks = await tasksRes.json();
    state.taskStats = await statsRes.json();

    // Update metric indicators
    const totalEl = document.getElementById("task-stat-total");
    const progressEl = document.getElementById("task-stat-progress");
    const doneEl = document.getElementById("task-stat-done");
    const criticalEl = document.getElementById("task-stat-critical");
    const badgeEl = document.getElementById("tasks-console-badge");
    const sidebarBadgeEl = document.getElementById("sidebar-task-mgmt-count");

    if (totalEl) totalEl.textContent = state.taskStats.total || 0;
    if (progressEl) progressEl.textContent = state.taskStats.in_progress || 0;
    if (doneEl) doneEl.textContent = `${state.taskStats.done || 0} (${state.taskStats.progress || 0}%)`;
    if (criticalEl) criticalEl.textContent = state.taskStats.critical || 0;
    if (badgeEl) badgeEl.textContent = `${state.taskStats.total || 0} Tasks Active`;
    if (sidebarBadgeEl) sidebarBadgeEl.textContent = state.taskStats.total || 0;

    filterTaskConsole();
  } catch (err) {
    console.error("Failed to load task console:", err);
    showToast("Error loading tasks: " + err.message, "error");
  }
}

function filterTaskConsole() {
  const container = document.getElementById("task-console-grid");
  if (!container) return;

  const searchQuery = (document.getElementById("task-search-input")?.value || "").toLowerCase().trim();
  const phaseFilter = document.getElementById("task-phase-filter")?.value || "all";
  const priorityFilter = document.getElementById("task-priority-filter")?.value || "all";
  const statusFilter = document.getElementById("task-status-filter")?.value || "all";

  let filtered = (state.tasks || []).filter(t => {
    // Search
    if (searchQuery) {
      const matchTitle = (t.title || "").toLowerCase().includes(searchQuery);
      const matchDesc = (t.description || "").toLowerCase().includes(searchQuery);
      const matchMcp = (t.assigned_mcp || "").toLowerCase().includes(searchQuery);
      if (!matchTitle && !matchDesc && !matchMcp) return false;
    }
    // Phase
    if (phaseFilter !== "all" && t.phase !== phaseFilter) return false;
    // Priority
    if (priorityFilter !== "all" && t.priority !== priorityFilter) return false;
    // Status
    if (statusFilter !== "all" && t.status !== statusFilter) return false;

    return true;
  });

  if (filtered.length === 0) {
    container.innerHTML = `
      <div class="p-8 rounded-xl border border-[#e4e4e7] bg-white text-center space-y-2">
        <div class="text-[15px] font-extrabold text-[#111]">No matching tasks found</div>
        <p class="text-[13px] text-zinc-500 font-bold">Try adjusting your search criteria or create a new custom task.</p>
        <button onclick="toggleAddTaskForm()" class="mt-2 h-9 px-4 rounded-lg bg-[#111] text-white text-[13px] font-bold hover:bg-zinc-800 transition-colors cursor-pointer">
          Create Task
        </button>
      </div>
    `;
    return;
  }

  container.innerHTML = filtered.map(t => {
    const isDone = t.status === "done";
    const isInProgress = t.status === "in_progress" || t.status === "active";
    
    let priorityClass = "bg-zinc-100 text-zinc-700";
    if (t.priority === "critical") priorityClass = "bg-red-100 text-red-900 border border-red-200";
    if (t.priority === "high") priorityClass = "bg-amber-100 text-amber-900 border border-amber-200";

    return `
      <div class="p-5 rounded-xl border border-[#e4e4e7] ${isDone ? 'bg-zinc-50/70 border-zinc-200 opacity-60' : 'bg-white hover:border-zinc-400'} transition-all space-y-3 shadow-2xs">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-zinc-100 pb-3">
          <div class="flex items-center gap-2 flex-wrap">
            <span class="px-2 py-0.5 rounded text-[12px] font-mono font-bold bg-[#111] text-white">
              ${escapeHtml(t.phase || 'Phase 1: Setup')}
            </span>
            <span class="px-2 py-0.5 rounded text-[11px] font-mono font-extrabold uppercase ${priorityClass}">
              ${escapeHtml(t.priority || 'high')}
            </span>
            ${t.assigned_mcp ? `
              <span class="px-2 py-0.5 rounded text-[11px] font-mono font-bold bg-zinc-100 text-zinc-800">
                Tool: ${escapeHtml(t.assigned_mcp)}
              </span>
            ` : ''}
          </div>
          
          <div class="flex items-center gap-2">
            <select onchange="updateTaskStatusFromConsole(${t.id}, this.value)" class="h-8 px-2 rounded-lg border border-[#e4e4e7] bg-white text-[12px] font-bold text-[#111] cursor-pointer">
              <option value="pending" ${t.status === 'pending' ? 'selected' : ''}>Pending</option>
              <option value="in_progress" ${isInProgress ? 'selected' : ''}>In Progress</option>
              <option value="done" ${isDone ? 'selected' : ''}>Completed</option>
            </select>
            <button onclick="openTaskEditModal(${t.id})" title="Edit Task" class="size-8 rounded-lg border border-[#e4e4e7] hover:bg-zinc-100 text-zinc-700 flex items-center justify-center cursor-pointer transition-colors">
              <svg class="size-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>
            </button>
            <button onclick="deleteTaskFromConsole(${t.id})" title="Delete Task" class="size-8 rounded-lg border border-[#e4e4e7] hover:bg-red-50 text-zinc-400 hover:text-red-600 flex items-center justify-center cursor-pointer transition-colors">
              <svg class="size-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
            </button>
          </div>
        </div>

        <div class="space-y-1">
          <div class="text-[15px] font-extrabold text-[#111] ${isDone ? 'line-through text-zinc-400' : ''}">
            ${escapeHtml(t.title)}
          </div>
          ${t.description ? `
            <p class="text-[13px] text-zinc-600 leading-relaxed font-bold">
              ${escapeHtml(t.description)}
            </p>
          ` : ''}
        </div>

        <div class="flex items-center justify-between pt-1 text-[12px] font-mono font-bold text-zinc-500">
          <span>Target Deadline: <strong class="text-[#111]">${escapeHtml(t.due_date || 'TBD')}</strong></span>
          <span class="text-zinc-400">ID #${t.id}</span>
        </div>
      </div>
    `;
  }).join("");
}

async function updateTaskStatusFromConsole(taskId, status) {
  try {
    await fetch(`/api/tasks/${taskId}/status`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status })
    });
    await loadAndRenderTaskConsole();
    await loadCalendar();
    updateRadarProgress();
    showToast(`Task status updated to ${status}`, "success", 2000);
  } catch (err) {
    showToast("Error updating task: " + err.message, "error");
  }
}

function openTaskEditModal(taskId) {
  const task = state.tasks.find(t => t.id === taskId);
  if (!task) return;

  const modal = document.getElementById("task-edit-modal");
  document.getElementById("edit-task-id").value = task.id;
  document.getElementById("edit-task-title").value = task.title || "";
  document.getElementById("edit-task-desc").value = task.description || "";
  document.getElementById("edit-task-phase").value = task.phase || "Phase 1: Setup";
  document.getElementById("edit-task-priority").value = task.priority || "high";
  document.getElementById("edit-task-due").value = task.due_date || "";
  document.getElementById("edit-task-mcp").value = task.assigned_mcp || "";

  if (modal) modal.classList.remove("hidden");
}

function closeTaskEditModal() {
  const modal = document.getElementById("task-edit-modal");
  if (modal) modal.classList.add("hidden");
}

async function handleSaveTaskEdit(e) {
  if (e) e.preventDefault();
  const taskId = document.getElementById("edit-task-id").value;
  const payload = {
    title: document.getElementById("edit-task-title").value.trim(),
    description: document.getElementById("edit-task-desc").value.trim(),
    phase: document.getElementById("edit-task-phase").value,
    priority: document.getElementById("edit-task-priority").value,
    due_date: document.getElementById("edit-task-due").value.trim(),
    assigned_mcp: document.getElementById("edit-task-mcp").value.trim()
  };

  try {
    const res = await fetch(`/api/tasks/${taskId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error("Server responded with " + res.status);

    closeTaskEditModal();
    await loadAndRenderTaskConsole();
    await loadCalendar();
    showToast("Task updated successfully", "success");
  } catch (err) {
    showToast("Failed to save task edit: " + err.message, "error");
  }
}

function deleteTaskFromConsole(taskId) {
  showConfirmModal(
    "Delete Task",
    "Are you sure you want to permanently remove this task from CHRONOS?",
    "Delete",
    async () => {
      try {
        await fetch(`/api/tasks/${taskId}`, { method: "DELETE" });
        await loadAndRenderTaskConsole();
        await loadCalendar();
        updateRadarProgress();
        showToast("Task removed from workspace", "info");
      } catch (err) {
        showToast("Failed to delete task: " + err.message, "error");
      }
    }
  );
}

// ── Agent Tool Builder & Diagnostics (/agent-tool-builder) ─────────────

async function loadAndRenderAgentTools() {
  try {
    const res = await fetch("/api/tools/catalog");
    state.agentTools = await res.json();
    renderAgentToolsCatalog();
  } catch (err) {
    console.error("Failed to load agent tools catalog:", err);
  }
}

function renderAgentToolsCatalog() {
  const container = document.getElementById("full-tools-catalog");
  if (!container) return;

  container.innerHTML = (state.agentTools || []).map(tool => {
    const diagnostic = state.toolDiagnostics[tool.id];
    const isHealthy = diagnostic ? diagnostic.success : true;
    const statusText = diagnostic ? diagnostic.status : "STANDBY";
    const latencyText = diagnostic ? `${diagnostic.latency_ms}ms` : "Unchecked";

    // Build parameter input markup
    const params = tool.parameters || {};
    const paramInputs = Object.entries(params).map(([paramName, paramDef]) => {
      const defaultValue = paramDef.default !== undefined ? paramDef.default : "";
      return `
        <div class="space-y-1">
          <div class="flex items-center justify-between text-[11px] font-mono text-zinc-500 font-bold">
            <span>${escapeHtml(paramName)} (${paramDef.type})</span>
            <span class="text-zinc-400">${paramDef.description || ''}</span>
          </div>
          <input type="text" id="param-${tool.id}-${paramName}" value="${escapeHtml(defaultValue)}" class="w-full h-8 px-2.5 rounded border border-[#e4e4e7] bg-zinc-50 text-[12px] font-mono font-bold text-[#111] focus:bg-white focus:outline-none focus:ring-1 focus:ring-[#111]">
        </div>
      `;
    }).join("");

    return `
      <div class="p-6 rounded-xl border border-[#e4e4e7] bg-white space-y-4 shadow-2xs hover:border-zinc-400 transition-all">
        <!-- Tool Header -->
        <div class="flex items-start justify-between gap-3 border-b border-zinc-100 pb-3">
          <div>
            <div class="flex items-center gap-2">
              <span class="text-[15px] font-extrabold text-[#111]">${escapeHtml(tool.name)}</span>
              <span class="px-1.5 py-0.5 rounded text-[11px] font-mono font-bold bg-zinc-100 text-zinc-700">v${tool.version}</span>
            </div>
            <div class="text-[12px] font-mono text-zinc-500 font-bold mt-0.5">${escapeHtml(tool.category)}</div>
          </div>
          <div class="flex items-center gap-1.5 px-2 py-1 rounded text-[11px] font-mono font-extrabold ${diagnostic && diagnostic.success ? 'bg-emerald-100 text-emerald-900 border border-emerald-200' : 'bg-zinc-100 text-zinc-700'}">
            <span class="size-1.5 rounded-full ${diagnostic && diagnostic.success ? 'bg-emerald-500' : 'bg-zinc-400'}"></span>
            <span>${statusText}</span>
          </div>
        </div>

        <!-- Description conforming to agent-tool-builder specs -->
        <p class="text-[13px] text-zinc-600 leading-relaxed font-bold">
          ${escapeHtml(tool.description)}
        </p>

        <!-- Parameters Schema -->
        <div class="space-y-2 pt-1 border-t border-zinc-100">
          <div class="text-[11px] font-mono uppercase tracking-wider text-zinc-400 font-extrabold">Schema Parameters:</div>
          <div class="space-y-2">
            ${paramInputs}
          </div>
        </div>

        <!-- Action Runner -->
        <div class="flex items-center justify-between pt-2">
          <button onclick="runToolDiagnostic('${tool.id}')" id="btn-test-${tool.id}" class="h-9 px-4 rounded-lg bg-[#111] text-white text-[13px] font-bold hover:bg-zinc-800 transition-colors flex items-center gap-1.5 cursor-pointer">
            <svg class="size-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>
            <span>Run Diagnostic</span>
          </button>
          <span class="text-[12px] font-mono font-bold text-zinc-400" id="latency-${tool.id}">Latency: ${latencyText}</span>
        </div>

        <!-- Expandable Execution Output -->
        <div id="output-${tool.id}" class="${diagnostic ? '' : 'hidden'} mt-3 p-3 rounded-lg bg-zinc-900 text-zinc-100 font-mono text-[12px] space-y-1">
          <div class="flex items-center justify-between text-[11px] text-zinc-400 border-b border-zinc-800 pb-1">
            <span>EXECUTION STDOUT</span>
            <span class="text-emerald-400 font-bold">${diagnostic?.status || 'OK'}</span>
          </div>
          <div class="overflow-x-auto whitespace-pre-wrap py-1 text-zinc-200">${escapeHtml(diagnostic?.stdout || '')}</div>
        </div>
      </div>
    `;
  }).join("");
}

async function runToolDiagnostic(toolId) {
  const tool = (state.agentTools || []).find(t => t.id === toolId);
  if (!tool) return;

  const btn = document.getElementById(`btn-test-${toolId}`);
  if (btn) btn.innerHTML = `<span class="thinking-dot"></span><span class="ml-2">Running...</span>`;

  // Collect parameters from inputs
  const params = {};
  for (const pName of Object.keys(tool.parameters || {})) {
    const inputEl = document.getElementById(`param-${toolId}-${pName}`);
    if (inputEl) params[pName] = inputEl.value;
  }

  try {
    const res = await fetch(`/api/tools/${toolId}/test`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ parameters: params })
    });
    const result = await res.json();
    state.toolDiagnostics[toolId] = result;

    renderAgentToolsCatalog();
    showToast(`Tool '${tool.name}' verified (${result.latency_ms}ms)`, result.success ? "success" : "warning");
  } catch (err) {
    showToast(`Diagnostic failed for ${tool.name}: ` + err.message, "error");
  } finally {
    if (btn) btn.innerHTML = `<span>Run Diagnostic</span>`;
  }
}

async function runAllToolHealthChecks() {
  showToast("Running diagnostics across all agent tools...", "info", 2000);
  for (const t of (state.agentTools || [])) {
    await runToolDiagnostic(t.id);
  }
  showToast("All agent tools health diagnostics completed.", "success");
}

function switchToolTab(tabName) {
  state.activeToolTab = tabName;
  const catalogBtn = document.getElementById("tool-tab-catalog");
  const configBtn = document.getElementById("tool-tab-configured");
  const catalogList = document.getElementById("full-tools-catalog");
  const configList = document.getElementById("full-mcps-list");

  if (tabName === "catalog") {
    if (catalogBtn) catalogBtn.className = "filter-btn filter-btn-active";
    if (configBtn) configBtn.className = "filter-btn";
    if (catalogList) catalogList.classList.remove("hidden");
    if (configList) configList.classList.add("hidden");
  } else {
    if (catalogBtn) catalogBtn.className = "filter-btn";
    if (configBtn) configBtn.className = "filter-btn filter-btn-active";
    if (catalogList) catalogList.classList.add("hidden");
    if (configList) configList.classList.remove("hidden");
  }
}

// ── Integrations Modal Controller ──────────────────────────────────────

async function openIntegrationsModal() {
  const modal = document.getElementById("integrations-modal");
  if (modal) modal.classList.remove("hidden");

  try {
    const res = await fetch("/api/integrations/status");
    const data = await res.json();
    const gcalBadge = document.getElementById("gcal-badge");
    const gcalText = document.getElementById("gcal-status-text");
    const waBadge = document.getElementById("wa-badge");

    if (gcalBadge && data.google_calendar) {
      gcalBadge.textContent = data.google_calendar.connected ? "Connected" : "Ready";
      gcalText.textContent = `Target: ${data.google_calendar.calendar_name}`;
    }
    if (waBadge && data.whatsapp) {
      waBadge.textContent = data.whatsapp.configured ? "Live API" : "Simulated Online";
    }
  } catch (err) {
    console.warn("Could not check integration statuses:", err);
  }
}

function closeIntegrationsModal() {
  const modal = document.getElementById("integrations-modal");
  if (modal) modal.classList.add("hidden");
}

async function triggerCalendarSync() {
  try {
    showToast("Synchronizing milestones with Google Calendar...", "info", 1800);
    const res = await fetch("/api/integrations/google-calendar/sync", { method: "POST" });
    const data = await res.json();
    if (data.success) {
      showToast(data.message, "success", 4000);
    } else {
      showToast("Sync warning: " + (data.message || "Failed to push"), "warning");
    }
  } catch (err) {
    showToast("Calendar sync failed: " + err.message, "error");
  }
}

async function triggerWhatsAppBriefing() {
  const phone = document.getElementById("wa-phone-input")?.value?.trim() || "+15550199";
  try {
    showToast(`Dispatching executive briefing to ${phone}...`, "info", 2000);
    const res = await fetch("/api/integrations/whatsapp/send", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ recipient: phone })
    });
    const data = await res.json();
    if (data.success) {
      showToast(`Briefing dispatched to ${phone} successfully.`, "success");
    } else {
      showToast("Dispatch error: " + (data.error || "Unknown"), "error");
    }
  } catch (err) {
    showToast("WhatsApp dispatch failed: " + err.message, "error");
  }
}

// ── MCP Catalog View ───────────────────────────────────────────────────

async function loadMcps() {
  try {
    const res = await fetch("/api/mcps");
    state.mcps = await res.json();
    
    const listEl = document.getElementById("sidebar-mcp-list");
    const moreEl = document.getElementById("sidebar-mcp-more");
    if (listEl) {
      const top3 = state.mcps.slice(0, 3);
      listEl.innerHTML = top3.map(m => `
        <div class="flex items-center justify-between text-[13px] font-mono">
          <span class="text-zinc-600 truncate">${escapeHtml(m.mcp_name)}</span>
          <span class="size-1.5 rounded-full bg-emerald-500 shrink-0"></span>
        </div>
      `).join("");
      
      if (moreEl) {
        if (state.mcps.length > 3) {
          moreEl.classList.remove("hidden");
          moreEl.textContent = `+${state.mcps.length - 3} more tools`;
        } else {
          moreEl.classList.add("hidden");
        }
      }
    }

    const countEl = document.getElementById("sidebar-mcp-count");
    if (countEl) countEl.textContent = state.mcps.length;

    if (state.activeView === 'mcps') renderFullMcps();
  } catch (err) {
    console.error("Failed to load MCPs:", err);
  }
}

function renderFullMcps() {
  const container = document.getElementById("full-mcps-list");
  if (!container) return;

  if (state.mcps.length === 0) {
    container.innerHTML = '<div class="text-[14px] text-zinc-500 col-span-2 p-6 bg-zinc-50 rounded-xl border border-[#e4e4e7]">No active MCP configurations yet. Ingest an event to generate.</div>';
    return;
  }

  container.innerHTML = state.mcps.map(m => `
    <div class="p-5 rounded-xl border border-[#e4e4e7] bg-white space-y-3 shadow-2xs">
      <div class="flex items-center justify-between">
        <span class="text-[15px] font-bold text-[#111]">${escapeHtml(m.mcp_name)}</span>
        <span class="px-2 py-0.5 rounded text-[12px] font-mono font-semibold bg-zinc-100 text-[#111]">
          ${m.is_installed ? 'Installed' : 'Ready'}
        </span>
      </div>
      <p class="text-[13px] text-zinc-600 leading-relaxed font-bold">${escapeHtml(m.description)}</p>
      <div class="flex items-center gap-2 pt-1">
        <code class="flex-1 text-[13px] font-mono font-semibold p-2 rounded bg-zinc-50 border border-[#e4e4e7] text-[#111] truncate">
          ${escapeHtml(m.install_command)}
        </code>
        <button onclick="copyToClipboard('${escapeHtml(m.install_command)}', this)" class="px-3 py-1.5 rounded bg-[#111] text-white text-[13px] font-semibold hover:bg-zinc-800 transition-colors cursor-pointer shrink-0">
          Copy
        </button>
      </div>
    </div>
  `).join("");
}

// ── Notification Channels & Pings ──────────────────────────────────────

async function loadChannels() {
  try {
    const res = await fetch("/api/channels");
    state.channels = await res.json();
    const badge = document.getElementById("sidebar-channel-badge");
    if (badge) {
      badge.className = state.channels.length > 0 ? "size-1.5 rounded-full bg-emerald-500" : "size-1.5 rounded-full bg-zinc-300";
    }
    if (state.activeView === 'channels') renderFullChannels();
  } catch (err) {
    console.error("Failed to load channels:", err);
  }
}

function renderFullChannels() {
  const container = document.getElementById("full-channels-list");
  if (!container) return;

  if (state.channels.length === 0) {
    container.innerHTML = '<div class="text-[14px] text-zinc-400 col-span-2">No external channels linked yet. Configure above.</div>';
    return;
  }

  container.innerHTML = state.channels.map(ch => `
    <div class="flex items-center justify-between p-3.5 rounded-xl border border-[#e4e4e7] bg-white shadow-2xs">
      <div>
        <span class="text-[13px] font-mono font-bold uppercase text-[#111]">[${escapeHtml(ch.platform)}]</span>
        <span class="text-[13px] text-zinc-700 ml-2 font-mono font-semibold">${escapeHtml(ch.target)}</span>
      </div>
      <div class="flex items-center gap-2">
        <button onclick="testChannelPing(${ch.id})" class="h-8 px-3 rounded-lg border border-[#e4e4e7] hover:bg-zinc-50 text-[13px] font-semibold text-zinc-800 transition-colors cursor-pointer">Ping</button>
        <button onclick="deleteChannel(${ch.id})" class="h-8 w-8 rounded-lg border border-[#e4e4e7] hover:bg-zinc-50 text-[14px] text-zinc-400 hover:text-[#111] flex items-center justify-center transition-colors cursor-pointer">&times;</button>
      </div>
    </div>
  `).join("");
}

async function saveAndTestChannel(platform, targetId, webhookId, tokenId) {
  const target = targetId ? (document.getElementById(targetId)?.value?.trim() || targetId) : "";
  const webhook_url = webhookId ? (document.getElementById(webhookId)?.value?.trim() || "") : "";
  const api_token = tokenId ? (document.getElementById(tokenId)?.value?.trim() || "") : "";

  if (!target && !webhook_url) {
    showToast(`Please provide target phone/ID or webhook URL for ${platform}`, "warning");
    return;
  }

  try {
    const res = await fetch("/api/channels", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        platform,
        target: target || `${platform}_channel`,
        webhook_url,
        api_token
      })
    });
    const data = await res.json();

    const pingRes = await fetch("/api/channels/test", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ channel_id: data.channel_id })
    });
    const pingData = await pingRes.json();

    showToast(`Connected to ${platform.toUpperCase()} (${pingData.detail || 'Verified'})`, "success");
    loadChannels();
  } catch (err) {
    showToast("Connection failed: " + err, "error");
  }
}

async function testChannelPing(channelId) {
  try {
    const res = await fetch("/api/channels/test", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ channel_id: channelId })
    });
    const data = await res.json();
    showToast(`Ping dispatched: ${data.detail || 'Success'}`, "success");
  } catch (err) {
    showToast("Ping failed: " + err, "error");
  }
}

function deleteChannel(channelId) {
  showConfirmModal(
    "Disconnect Channel",
    "Disconnect this notification channel from receiving executive alerts?",
    "Disconnect",
    async () => {
      try {
        await fetch(`/api/channels/${channelId}`, { method: "DELETE" });
        loadChannels();
        showToast("Channel disconnected", "info");
      } catch (e) {
        showToast("Failed to disconnect channel: " + e, "error");
      }
    }
  );
}

async function exportMcpConfig() {
  try {
    const res = await fetch("/api/mcps/export-config", { method: "POST" });
    const data = await res.json();
    showToast(`Exported mcp_servers.json successfully`, "success");
  } catch (err) {
    showToast("Export failed: " + err, "error");
  }
}

function copyToClipboard(text, btn) {
  navigator.clipboard.writeText(text).then(() => {
    const original = btn.textContent;
    btn.textContent = "Copied!";
    showToast("Command copied to clipboard", "info", 1500);
    setTimeout(() => { btn.textContent = original; }, 2000);
  });
}

// ── Markdown Parser ────────────────────────────────────────────────────

function formatMarkdown(text) {
  if (!text) return "";
  let html = escapeHtml(text);

  // Bold
  html = html.replace(/\*\*(.*?)\*\*/g, '<strong class="font-extrabold text-[#111]">$1</strong>');
  // Inline Code
  html = html.replace(/`(.*?)`/g, '<code class="font-mono text-[13px] bg-zinc-100 text-[#111] border border-[#e4e4e7] px-1.5 py-0.5 rounded">$1</code>');
  // Numbered list items
  html = html.replace(/^(\d+)\.\s+(.*)$/gm, '<div class="flex items-start gap-2.5 my-2"><span class="shrink-0 font-mono text-[13px] font-bold text-[#111] bg-zinc-100 rounded px-1.5 py-0.5 border border-[#e4e4e7]">$1</span><span class="text-[#111] text-[15px] font-bold leading-relaxed">$2</span></div>');
  // Bullet list items
  html = html.replace(/^[-*]\s+(.*)$/gm, '<div class="flex items-start gap-2.5 my-1.5"><span class="size-1.5 rounded-full bg-[#111] mt-2 shrink-0"></span><span class="text-[#111] text-[15px] font-bold leading-relaxed">$1</span></div>');
  // Paragraphs & Line breaks
  html = html.replace(/\n\n/g, '<div class="h-2.5"></div>');
  html = html.replace(/\n/g, '<br>');

  return html;
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

// ── Chat History Drawer & Session Export ───────────────────────────────

function toggleChatHistoryDrawer() {
  const drawer = document.getElementById("chat-history-drawer");
  const backdrop = document.getElementById("chat-history-backdrop");
  if (!drawer) return;

  const isClosed = drawer.classList.contains("translate-x-full");
  if (isClosed) {
    drawer.classList.remove("translate-x-full");
    if (backdrop) backdrop.classList.remove("hidden");
    renderChatHistoryDrawer();
  } else {
    drawer.classList.add("translate-x-full");
    if (backdrop) backdrop.classList.add("hidden");
  }
}

function renderChatHistoryDrawer() {
  const container = document.getElementById("chat-history-list");
  if (!container) return;

  const msgCount = (state.chatHistory || []).length;
  const userMessages = (state.chatHistory || []).filter(m => m.role === "user");
  const firstPrompt = userMessages.length > 0 ? userMessages[0].content : "Initial workspace session";
  const lastActive = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  container.innerHTML = `
    <!-- Active Current Session Card -->
    <div class="p-4 rounded-xl border-2 border-[#111] bg-white space-y-2 shadow-2xs">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-2">
          <span class="size-2 rounded-full bg-emerald-500 animate-pulse"></span>
          <span class="text-[12px] font-mono font-extrabold uppercase text-[#111]">Active Session</span>
        </div>
        <span class="text-[11px] font-mono text-zinc-400 font-bold">${lastActive}</span>
      </div>
      <div class="text-[14px] font-extrabold text-[#111] line-clamp-2">
        "${escapeHtml(firstPrompt)}"
      </div>
      <div class="flex items-center justify-between pt-1 text-[12px] font-mono text-zinc-500 font-bold">
        <span>${msgCount} messages in thread</span>
        <span class="text-emerald-700 font-extrabold">Live SQLite</span>
      </div>
    </div>

    <!-- Session Guidance -->
    <div class="p-4 rounded-xl border border-[#e4e4e7] bg-zinc-50 space-y-2">
      <div class="text-[12px] font-mono uppercase text-zinc-500 font-bold">Persistence &amp; Storage</div>
      <p class="text-[13px] text-zinc-600 font-bold leading-relaxed">
        All chat messages, research cards, and tool states are automatically saved to local SQLite (<code class="bg-zinc-200 px-1 py-0.5 rounded font-mono text-xs">chronos.db</code>).
      </p>
      <div class="text-[12px] font-mono text-zinc-500 font-semibold pt-1">
        • Click <strong>Export (.md)</strong> above to download markdown notes.<br>
        • Click <strong>Clear Thread</strong> to start a fresh sprint.
      </div>
    </div>
  `;
}

function exportChatTranscript() {
  if (!state.chatHistory || state.chatHistory.length === 0) {
    showToast("No chat history to export.", "warning");
    return;
  }

  let md = `# CHRONOS Sentinel // Chat Session Transcript\n`;
  md += `Exported: ${new Date().toISOString()}\n`;
  md += `Active Model: ${state.activeModel} (${state.activeProvider})\n\n`;
  md += `---\n\n`;

  state.chatHistory.forEach((msg, idx) => {
    const roleTitle = msg.role === 'user' ? 'USER' : 'CHRONOS SENTINEL';
    md += `### [${idx + 1}] ${roleTitle}\n\n`;
    md += `${msg.content}\n\n`;
    if (msg.card_type) {
      md += `*Attached Action Card: ${msg.card_type}*\n\n`;
    }
    md += `---\n\n`;
  });

  const blob = new Blob([md], { type: "text/markdown;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `chronos_session_${new Date().toISOString().substring(0, 10)}.md`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);

  showToast("Chat session exported to markdown successfully.", "success");
}

function clearChatHistoryConfirm() {
  showConfirmModal(
    "Clear Conversation History",
    "This will permanently delete all conversation messages from local SQLite. Milestones and MCPs will remain intact.",
    "Clear All",
    async () => {
      try {
        await resetChat();
        toggleChatHistoryDrawer();
        showToast("Conversation thread cleared.", "info");
      } catch (err) {
        showToast("Error clearing chat: " + err.message, "error");
      }
    }
  );
}

// ── Deadline Radar Adjuster & Buffer System ─────────────────────────────

function openDeadlineModal() {
  const modal = document.getElementById("deadline-modal");
  if (!modal) return;

  const titleInput = document.getElementById("deadline-modal-title");
  const dateInput = document.getElementById("deadline-modal-date");

  if (titleInput && state.activeEvent) {
    titleInput.value = state.activeEvent.title || "";
  }
  if (dateInput) {
    if (state.activeEvent && state.activeEvent.deadline) {
      dateInput.value = state.activeEvent.deadline.substring(0, 16).replace("T", " ");
    } else {
      const future = new Date(Date.now() + 48 * 3600 * 1000);
      dateInput.value = future.toISOString().substring(0, 16).replace("T", " ");
    }
  }

  modal.classList.remove("hidden");
}

function closeDeadlineModal() {
  const modal = document.getElementById("deadline-modal");
  if (modal) modal.classList.add("hidden");
}

function setQuickDate(hours) {
  const dateInput = document.getElementById("deadline-modal-date");
  if (!dateInput) return;

  const base = new Date();
  base.setTime(base.getTime() + hours * 3600 * 1000);
  
  const yyyy = base.getFullYear();
  const mm = String(base.getMonth() + 1).padStart(2, '0');
  const dd = String(base.getDate()).padStart(2, '0');
  const hh = String(base.getHours()).padStart(2, '0');
  const min = String(base.getMinutes()).padStart(2, '0');

  dateInput.value = `${yyyy}-${mm}-${dd} ${hh}:${min}`;
}

async function handleSaveDeadline(e) {
  if (e) e.preventDefault();

  const title = document.getElementById("deadline-modal-title")?.value?.trim();
  const dateStr = document.getElementById("deadline-modal-date")?.value?.trim();

  if (!title || !dateStr) {
    showToast("Please provide both event title and target deadline.", "warning");
    return;
  }

  const eventId = state.activeEvent ? state.activeEvent.id : 1;
  const isoDeadline = dateStr.includes("T") ? dateStr : dateStr.replace(" ", "T") + ":00Z";

  try {
    const res = await fetch(`/api/events/${eventId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        title: title,
        deadline: isoDeadline,
        status: "active"
      })
    });

    if (!res.ok) throw new Error("Server responded with HTTP " + res.status);
    const data = await res.json();

    state.activeEvent = data.event;
    state.targetDeadline = new Date(isoDeadline.replace("Z", ""));

    const titleEl = document.getElementById("radar-event-title");
    if (titleEl) titleEl.textContent = title;

    closeDeadlineModal();
    await loadCalendar();
    await loadBriefing();
    showToast("Deadline Radar updated successfully! Countdown resumed.", "success");
  } catch (err) {
    showToast("Failed to update deadline: " + err.message, "error");
  }
}

async function quickExtendDeadline(hours) {
  const eventId = state.activeEvent ? state.activeEvent.id : 1;
  const currentTitle = state.activeEvent ? state.activeEvent.title : "Project Sprint Deadline";

  // Calculate new target: if expired or past, extend from NOW; otherwise extend from current deadline
  let baseTime = Date.now();
  if (state.targetDeadline && state.targetDeadline.getTime() > baseTime) {
    baseTime = state.targetDeadline.getTime();
  }
  const newDate = new Date(baseTime + hours * 3600 * 1000);
  const isoDeadline = newDate.toISOString();

  try {
    const res = await fetch(`/api/events/${eventId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        title: currentTitle,
        deadline: isoDeadline,
        status: "active"
      })
    });

    if (!res.ok) throw new Error("HTTP " + res.status);
    const data = await res.json();

    state.activeEvent = data.event;
    state.targetDeadline = newDate;

    await loadCalendar();
    await loadBriefing();
    showToast(`+${hours}h buffer added to Deadline Radar!`, "success");
  } catch (err) {
    showToast("Failed to extend deadline: " + err.message, "error");
  }
}

// ── External Connectors Hub View ───────────────────────────────────────

async function loadAndRenderConnectors() {
  try {
    const res = await fetch("/api/integrations/status");
    const data = await res.json();

    const gcalBadge = document.getElementById("gcal-badge");
    const gcalText = document.getElementById("gcal-status-text");
    if (gcalBadge && data.google_calendar) {
      gcalBadge.textContent = data.google_calendar.connected ? "Connected" : "Ready";
      if (gcalText) gcalText.textContent = `Target: ${data.google_calendar.calendar_name}`;
    }

    const waBadge = document.getElementById("wa-badge");
    if (waBadge && data.whatsapp) {
      waBadge.textContent = data.whatsapp.configured ? "Graph API v21.0 Online" : "Simulated Active";
    }
  } catch (err) {
    console.warn("Could not refresh connector indicators:", err);
  }
}

async function triggerWhatsAppBriefingFromConnectors() {
  const phone = document.getElementById("connectors-wa-phone")?.value?.trim() || "+15550199";
  try {
    showToast(`Dispatching live sentinel alert to ${phone}...`, "info", 1800);
    const res = await fetch("/api/integrations/whatsapp/send", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ recipient: phone })
    });
    const data = await res.json();
    if (data.success) {
      showToast(`Executive briefing delivered to ${phone}`, "success", 4000);
    } else {
      showToast("Dispatch error: " + (data.error || "Unknown"), "error");
    }
  } catch (err) {
    showToast("WhatsApp alert failed: " + err.message, "error");
  }
}
