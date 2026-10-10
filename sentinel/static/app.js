/* ==========================================================================
   CHRONOS // CLIENT APPLICATION SCRIPT
   Pure White Editorial Minimalist Chatbot with Progressive Disclosure
   Font: Satoshi | Zero Emojis | Vector SVGs
   ========================================================================== */

let state = {
  chatHistory: [],
  channels: [],
  calendar: [],
  mcps: [],
  briefing: null
};

document.addEventListener("DOMContentLoaded", () => {
  initLiveClock();
  loadChatHistory();
  loadBriefing();
  loadChannels();
  
  // Refresh briefing periodically
  setInterval(loadBriefing, 15000);
});

// Live Clock
function initLiveClock() {
  const clockEl = document.getElementById("live-clock");
  const update = () => {
    const now = new Date();
    clockEl.textContent = now.toTimeString().split(" ")[0];
  };
  update();
  setInterval(update, 1000);
}

// Executive Briefing Ticker
async function loadBriefing() {
  try {
    const res = await fetch("/api/briefing");
    const data = await res.json();
    state.briefing = data;
    const tickerText = document.getElementById("ticker-text");
    if (tickerText) {
      tickerText.textContent = `[BRIEFING] ${data.message || 'All systems nominal.'}`;
    }
  } catch (err) {
    console.error("Failed to load briefing:", err);
  }
}

// Chat Engine
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

  container.innerHTML = state.chatHistory.map(msg => renderMessageHtml(msg)).join("");
  scrollToBottom();
}

function renderMessageHtml(msg) {
  const isUser = msg.role === "user";
  const formattedContent = formatMarkdown(msg.content);

  let cardHtml = "";
  if (msg.card_type === "research_brief" && msg.metadata) {
    cardHtml = renderResearchCard(msg.metadata);
  } else if (msg.card_type === "tasks_and_mcps" && msg.metadata) {
    cardHtml = renderTasksAndMcpsCard(msg.metadata);
  } else if (msg.card_type === "briefing_card" && msg.metadata) {
    cardHtml = renderBriefingCard(msg.metadata);
  } else if (msg.card_type === "channel_connect_trigger") {
    cardHtml = `
      <div class="chat-card">
        <button class="btn btn-primary btn-sm" onclick="openDrawer('channels')">
          Configure WhatsApp & Social Notifications
        </button>
      </div>
    `;
  }

  const botSvg = `
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <path d="M12 8V4H8"></path>
      <rect x="4" y="8" width="16" height="12" rx="2"></rect>
      <path d="M2 14h2"></path>
      <path d="M20 14h2"></path>
      <path d="M9 13v2"></path>
      <path d="M15 13v2"></path>
    </svg>
  `;

  const userSvg = `
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
      <circle cx="12" cy="7" r="4"></circle>
    </svg>
  `;

  return `
    <div class="message-row ${isUser ? 'user' : 'assistant'}">
      ${!isUser ? `<div class="avatar-badge assistant">${botSvg}</div>` : ''}
      <div class="message-body">
        <div class="message-bubble">
          ${formattedContent}
          ${cardHtml}
        </div>
      </div>
      ${isUser ? `<div class="avatar-badge user">${userSvg}</div>` : ''}
    </div>
  `;
}

function renderResearchCard(meta) {
  return `
    <div class="chat-card">
      <div class="chat-card-header">
        <span class="chat-card-title">PRE-RESEARCH DOSSIER // ${escapeHtml(meta.event_title || '')}</span>
      </div>
      <div style="font-size: 13px; color: var(--text-secondary); margin-bottom: 12px; line-height: 1.6;">
        ${escapeHtml(meta.summary || '')}
      </div>
      <div style="font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.04em; margin-top: 14px; color: var(--text-primary);">
        Quick Select Your Focus Track:
      </div>
      <div class="chip-group">
        <button class="choice-chip" onclick="quickSend('I want to prioritize Track 1 with Python backend and solo builder mode')">
          <span>Track 1: Autonomous Agent (Python)</span>
        </button>
        <button class="choice-chip" onclick="quickSend('Solo builder mode with full-stack UI, Chrome DevTools testing')">
          <span>Solo Builder (Full-Stack UI)</span>
        </button>
        <button class="choice-chip" onclick="quickSend('Configure backend with SQLite, GitHub MCP, and auto-commits')">
          <span>Backend Logic + GitHub MCP</span>
        </button>
      </div>
    </div>
  `;
}

function renderTasksAndMcpsCard(meta) {
  const tasks = meta.tasks || [];
  const mcps = meta.mcps || [];

  const tasksHtml = tasks.map(t => `
    <div class="chat-task-item ${t.status === 'done' ? 'done' : ''}">
      <input type="checkbox" class="chat-task-cb" ${t.status === 'done' ? 'checked' : ''} onchange="toggleTaskInChat(${t.id}, this.checked)">
      <div style="flex: 1;">
        <div style="font-size: 13px; font-weight: 600;">${escapeHtml(t.title)}</div>
        <div style="font-family: var(--font-mono); font-size: 11px; color: var(--text-muted); margin-top: 2px;">
          <span>${t.phase}</span> • <span>Due: ${t.due_date || 'TBD'}</span>
          ${t.assigned_mcp ? ` • <span>Tool: <code>${escapeHtml(t.assigned_mcp)}</code></span>` : ''}
        </div>
      </div>
    </div>
  `).join("");

  const mcpsHtml = mcps.slice(0, 3).map(m => `
    <div class="chat-mcp-item">
      <span><strong>${escapeHtml(m.name)}</strong></span>
      <code>${escapeHtml(m.install_command)}</code>
    </div>
  `).join("");

  return `
    <div class="chat-card">
      <div class="chat-card-header">
        <span class="chat-card-title">PHASED ROADMAP & RESOLVED MCP TOOLING</span>
        <button class="btn btn-subtle btn-sm" onclick="openDrawer('matrix')">Full Matrix</button>
      </div>
      <div style="margin-bottom: 16px;">
        ${tasksHtml}
      </div>
      <div class="chat-card-title" style="margin-top: 18px; margin-bottom: 8px;">RECOMMENDED MCP SERVERS</div>
      <div>
        ${mcpsHtml}
      </div>
      <div style="margin-top: 14px; display: flex; gap: 10px;">
        <button class="btn btn-primary btn-sm" onclick="exportMcpConfig()">
          Export ` + "`mcp_servers.json`" + `
        </button>
        <button class="btn btn-subtle btn-sm" onclick="openDrawer('channels')">
          Connect WhatsApp Alerts
        </button>
      </div>
    </div>
  `;
}

function renderBriefingCard(meta) {
  const briefing = meta.briefing || {};
  return `
    <div class="chat-card" style="border-left: 3px solid #000000;">
      <div class="chat-card-header">
        <span class="chat-card-title">${escapeHtml(briefing.header || 'EXECUTIVE BRIEFING')}</span>
      </div>
      <div style="font-size: 14px; font-weight: 600; color: var(--text-primary); margin-bottom: 10px;">
        ${escapeHtml(briefing.message || '')}
      </div>
      <button class="btn btn-subtle btn-sm" onclick="openDrawer('matrix')">View Schedule Matrix</button>
    </div>
  `;
}

async function handleSend(e) {
  if (e) e.preventDefault();
  const input = document.getElementById("chat-input");
  const text = input.value.trim();
  if (!text) return;

  input.value = "";

  // Optimistic User Message
  state.chatHistory.push({
    role: "user",
    content: text,
    card_type: null,
    metadata: {}
  });
  renderChat();

  // Show Typing Indicator
  const container = document.getElementById("chat-history");
  const typingRow = document.createElement("div");
  typingRow.id = "typing-indicator";
  typingRow.className = "message-row assistant";
  typingRow.innerHTML = `
    <div class="avatar-badge assistant">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M12 8V4H8"></path>
        <rect x="4" y="8" width="16" height="12" rx="2"></rect>
      </svg>
    </div>
    <div class="message-body">
      <div class="message-bubble" style="color: var(--text-muted); font-family: var(--font-mono); font-size: 12px;">
        Analyzing input & resolving MCP configurations...
      </div>
    </div>
  `;
  container.appendChild(typingRow);
  scrollToBottom();

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text })
    });
    const reply = await res.json();

    // Remove typing indicator
    const ti = document.getElementById("typing-indicator");
    if (ti) ti.remove();

    state.chatHistory.push(reply);
    renderChat();
    loadBriefing();
  } catch (err) {
    const ti = document.getElementById("typing-indicator");
    if (ti) ti.remove();
    alert("Chat error: " + err);
  }
}

function quickSend(text) {
  document.getElementById("chat-input").value = text;
  handleSend(null);
}

async function toggleTaskInChat(taskId, isChecked) {
  const newStatus = isChecked ? 'done' : 'pending';
  try {
    await fetch(`/api/tasks/${taskId}/status`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: newStatus })
    });
    loadBriefing();
  } catch (err) {
    console.error("Error updating task status:", err);
  }
}

async function resetChat() {
  if (confirm("Reset current chat stream?")) {
    await fetch("/api/chat/reset", { method: "POST" });
    state.chatHistory = [];
    loadChatHistory();
  }
}

function scrollToBottom() {
  const container = document.getElementById("chat-history");
  if (container) {
    container.scrollTop = container.scrollHeight;
  }
}

// Drawer Controls
function openDrawer(name) {
  const drawer = document.getElementById(`drawer-${name}`);
  if (drawer) {
    drawer.classList.add("active");
    if (name === "channels") loadChannels();
    if (name === "matrix") loadDrawerCalendar();
    if (name === "mcps") loadDrawerMcps();
  }
}

function closeDrawer(name) {
  const drawer = document.getElementById(`drawer-${name}`);
  if (drawer) drawer.classList.remove("active");
}

function closeDrawerOnBackdrop(e, name) {
  if (e.target.id === `drawer-${name}`) {
    closeDrawer(name);
  }
}

// Social Media & Messaging Channels (WhatsApp, Telegram, Discord, Slack)
async function loadChannels() {
  try {
    const res = await fetch("/api/channels");
    const channels = await res.json();
    state.channels = channels;
    renderChannelsList();
  } catch (err) {
    console.error("Failed to load channels:", err);
  }
}

function renderChannelsList() {
  const container = document.getElementById("active-channels-list");
  if (!container) return;

  if (state.channels.length === 0) {
    container.innerHTML = '<div style="font-size: 12px; color: var(--text-muted);">No external channels linked yet. Configure above.</div>';
    return;
  }

  container.innerHTML = state.channels.map(ch => `
    <div style="display: flex; justify-content: space-between; align-items: center; padding: 10px 14px; background: #ffffff; border: 1px solid var(--border-default); border-radius: 6px; margin-bottom: 8px;">
      <div>
        <span style="font-family: var(--font-mono); font-size: 11px; font-weight: 700; text-transform: uppercase;">[${escapeHtml(ch.platform)}]</span>
        <span style="font-size: 13px; margin-left: 8px;">${escapeHtml(ch.target)}</span>
      </div>
      <div style="display: flex; gap: 8px;">
        <button class="btn btn-subtle btn-sm" onclick="testChannelPing(${ch.id})">Ping</button>
        <button class="btn btn-subtle btn-sm" onclick="deleteChannel(${ch.id})">&times;</button>
      </div>
    </div>
  `).join("");
}

async function saveAndTestChannel(platform, targetId, webhookId, tokenId) {
  const target = targetId ? (document.getElementById(targetId)?.value?.trim() || targetId) : "";
  const webhook_url = webhookId ? (document.getElementById(webhookId)?.value?.trim() || "") : "";
  const api_token = tokenId ? (document.getElementById(tokenId)?.value?.trim() || "") : "";

  if (!target && !webhook_url) {
    alert(`Please provide target phone/ID or webhook URL for ${platform}.`);
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

    // Trigger immediate verification ping
    const pingRes = await fetch("/api/channels/test", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ channel_id: data.channel_id })
    });
    const pingData = await pingRes.json();

    alert(`Connected to ${platform.toUpperCase()}!\nStatus: ${pingData.detail || 'Verified'}`);
    loadChannels();
  } catch (err) {
    alert("Connection failed: " + err);
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
    alert(`Ping dispatched!\nResult: ${data.detail || 'Success'}`);
  } catch (err) {
    alert("Ping failed: " + err);
  }
}

async function deleteChannel(channelId) {
  await fetch(`/api/channels/${channelId}`, { method: "DELETE" });
  loadChannels();
}

// Drawer Calendar
async function loadDrawerCalendar() {
  const container = document.getElementById("drawer-calendar-list");
  try {
    const res = await fetch("/api/calendar");
    const data = await res.json();

    if (data.length === 0) {
      container.innerHTML = '<div style="font-size: 13px; color: var(--text-muted);">No schedule items. Drop a hackathon link in chat.</div>';
      return;
    }

    container.innerHTML = data.map(item => {
      const isDeadline = item.type === 'event_deadline';
      return `
        <div style="padding: 12px; border-bottom: 1px solid var(--border-subtle); ${isDeadline ? 'background: #fafafa; border-left: 3px solid #000000;' : ''}">
          <div style="font-family: var(--font-mono); font-size: 11px; color: var(--text-muted);">${item.date || 'TBD'}</div>
          <div style="font-size: 13px; font-weight: 600; color: #000000; margin-top: 3px;">
            ${escapeHtml(item.title)}
          </div>
          ${item.assigned_mcp ? `<div style="font-family: var(--font-mono); font-size: 11px; color: var(--text-muted); margin-top: 2px;">Tool: ${escapeHtml(item.assigned_mcp)}</div>` : ''}
        </div>
      `;
    }).join("");
  } catch (err) {
    console.error("Failed to load calendar matrix:", err);
  }
}

// Drawer MCPs
async function loadDrawerMcps() {
  const container = document.getElementById("drawer-mcps-list");
  try {
    const res = await fetch("/api/mcps");
    const data = await res.json();

    if (data.length === 0) {
      container.innerHTML = '<div style="font-size: 13px; color: var(--text-muted);">No MCPs configured yet.</div>';
      return;
    }

    container.innerHTML = data.map(m => `
      <div style="padding: 14px; background: var(--bg-subtle); border: 1px solid var(--border-default); border-radius: 6px; margin-bottom: 10px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
          <strong style="font-size: 13px;">${escapeHtml(m.mcp_name)}</strong>
          <span style="font-family: var(--font-mono); font-size: 10px; padding: 2px 6px; background: #ffffff; border: 1px solid var(--border-default); border-radius: 4px;">
            ${m.is_installed ? 'Installed' : 'Ready'}
          </span>
        </div>
        <div style="font-size: 12px; color: var(--text-secondary); margin-bottom: 8px;">${escapeHtml(m.description)}</div>
        <code style="display: block; font-family: var(--font-mono); font-size: 11px; padding: 6px 8px; background: #ffffff; border: 1px solid var(--border-default); border-radius: 4px;">
          ${escapeHtml(m.install_command)}
        </code>
      </div>
    `).join("");
  } catch (err) {
    console.error("Failed to load MCPs:", err);
  }
}

async function exportMcpConfig() {
  try {
    const res = await fetch("/api/mcps/export-config", { method: "POST" });
    const data = await res.json();
    alert(`Configuration exported successfully to:\n${data.filepath}`);
  } catch (err) {
    alert("Export failed: " + err);
  }
}

// Helper: Simple Markdown formatting for chat
function formatMarkdown(text) {
  if (!text) return "";
  let html = escapeHtml(text);

  // Bold
  html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  // Inline Code
  html = html.replace(/`(.*?)`/g, '<code>$1</code>');
  // Hyphen bullet lists
  html = html.replace(/^-\s+(.*)$/gm, '<p style="margin-left: 14px; margin-bottom: 4px;">- $1</p>');
  // Line breaks
  html = html.replace(/\n\n/g, '<br><br>');
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
