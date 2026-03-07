(function () {
  const STORAGE_KEY = 'ai-teacher-chats';
  const messagesEl = document.getElementById('messages');
  const welcomeEl = document.getElementById('welcome');
  const inputEl = document.getElementById('input');
  const sendBtn = document.getElementById('sendBtn');
  const newChatBtn = document.getElementById('newChatBtn');
  const chatListEl = document.getElementById('chatList');
  const sidebarToggle = document.getElementById('sidebarToggle');
  const sidebar = document.getElementById('sidebar');
  const backendBadge = document.getElementById('backendBadge');

  if (!messagesEl || !inputEl || !sendBtn) return;

  /** All chats: [{ id, title, messages: [{ role, content }], createdAt }, ...] */
  let chats = loadChats();
  /** Id of the chat currently shown (null = new empty chat) */
  let currentChatId = null;

  function loadChats() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) {
        const data = JSON.parse(raw);
        return Array.isArray(data) ? data : [];
      }
    } catch (_) {}
    return [];
  }

  function saveChats() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(chats));
    } catch (_) {}
  }

  function generateId() {
    return 'chat-' + Date.now() + '-' + Math.random().toString(36).slice(2, 9);
  }

  function getCurrentChat() {
    if (!currentChatId) return null;
    return chats.find(function (c) { return c.id === currentChatId; }) || null;
  }

  function getCurrentHistory() {
    const chat = getCurrentChat();
    return chat ? chat.messages.slice() : [];
  }

  function renderChatList() {
    if (!chatListEl) return;
    chatListEl.innerHTML = '';
    // Newest first
    var list = chats.slice().sort(function (a, b) {
      return (b.createdAt || 0) - (a.createdAt || 0);
    });
    list.forEach(function (chat) {
      var btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'chat-item' + (chat.id === currentChatId ? ' active' : '');
      btn.setAttribute('role', 'listitem');
      btn.textContent = chat.title || 'New chat';
      btn.addEventListener('click', function () {
        switchToChat(chat.id);
        if (sidebar) sidebar.classList.remove('open');
      });
      chatListEl.appendChild(btn);
    });
  }

  function switchToChat(id) {
    currentChatId = id;
    renderChatList();
    showCurrentChat();
  }

  function showCurrentChat() {
    // Clear messages area (keep welcome node to reuse)
    var toRemove = messagesEl.querySelectorAll('.message, .loading-row');
    toRemove.forEach(function (n) { n.remove(); });

    var chat = getCurrentChat();
    if (chat && chat.messages.length > 0) {
      if (welcomeEl) welcomeEl.style.display = 'none';
      chat.messages.forEach(function (msg) {
        var role = msg.role === 'assistant' ? 'teacher' : msg.role;
        addMessageToDOM(role, msg.content, false);
      });
    } else {
      if (welcomeEl) welcomeEl.style.display = '';
    }
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  function startNewChat() {
    currentChatId = null;
    renderChatList();
    if (welcomeEl) welcomeEl.style.display = '';
    var toRemove = messagesEl.querySelectorAll('.message, .loading-row');
    toRemove.forEach(function (n) { n.remove(); });
    if (sidebar) sidebar.classList.remove('open');
  }

  function ensureCurrentChat() {
    if (currentChatId) return getCurrentChat();
    var chat = {
      id: generateId(),
      title: 'New chat',
      messages: [],
      createdAt: Date.now(),
    };
    chats.push(chat);
    currentChatId = chat.id;
    saveChats();
    renderChatList();
    return chat;
  }

  function updateChatTitle(chat, firstLine) {
    var title = (firstLine || '').trim().slice(0, 40);
    if (title) {
      chat.title = title;
      saveChats();
      renderChatList();
    }
  }

  // Marked + highlight.js
  if (typeof marked !== 'undefined') {
    marked.setOptions({
      gfm: true,
      breaks: true,
      highlight: function (code, lang) {
        if (typeof hljs !== 'undefined' && lang) {
          try {
            return hljs.highlight(code, { language: lang }).value;
          } catch (_) {}
        }
        return code;
      },
    });
  }

  function escapeHtml(text) {
    var div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  function renderMarkdown(text) {
    if (typeof marked !== 'undefined') {
      try {
        return marked.parse(text || '');
      } catch (_) {}
    }
    return escapeHtml(text || '').replace(/\n/g, '<br>');
  }

  function addMessageToDOM(role, content, isError) {
    var div = document.createElement('div');
    div.className = 'message message-' + role + (isError ? ' message-error' : '');
    div.setAttribute('data-role', role);

    var avatar = role === 'user' ? 'You' : 'T';
    var isMd = role === 'teacher' && !isError;
    var body = isMd ? renderMarkdown(content) : escapeHtml(content).replace(/\n/g, '<br>');

    div.innerHTML =
      '<div class="message-avatar" aria-hidden="true">' + avatar + '</div>' +
      '<div class="message-body">' +
      '<div class="message-content markdown-body">' + body + '</div>' +
      '</div>';
    messagesEl.appendChild(div);
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  function addLoading() {
    var div = document.createElement('div');
    div.className = 'loading-row';
    div.id = 'loading-row';
    div.innerHTML =
      '<div class="message-avatar">T</div>' +
      '<div class="loading-dots">' +
      '<span></span><span></span><span></span>' +
      '</div>' +
      '<span>Thinking…</span>';
    messagesEl.appendChild(div);
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  function removeLoading() {
    var el = document.getElementById('loading-row');
    if (el) el.remove();
  }

  async function send() {
    var text = inputEl.value.trim();
    if (!text) return;

    inputEl.value = '';
    inputEl.style.height = 'auto';

    var chat = ensureCurrentChat();
    var history = chat.messages.slice();

    if (welcomeEl) welcomeEl.style.display = 'none';
    addMessageToDOM('user', text);
    addLoading();
    sendBtn.disabled = true;

    try {
      var res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, history: history }),
      });
      var data = await res.json().catch(function () { return {}; });
      removeLoading();
      if (res.ok && data.reply != null) {
        addMessageToDOM('teacher', data.reply);
        chat.messages.push({ role: 'user', content: text });
        chat.messages.push({ role: 'assistant', content: data.reply });
        if (chat.title === 'New chat') {
          updateChatTitle(chat, text.split('\n')[0]);
        }
        saveChats();
      } else {
        var errMsg = data.detail || data.error || 'Something went wrong.';
        if (res.status === 429) errMsg = 'Too many requests. Please try again later.';
        else if (res.status === 503) errMsg = 'Service temporarily unavailable. Please try again.';
        addMessageToDOM('teacher', errMsg, true);
      }
    } catch (err) {
      removeLoading();
      addMessageToDOM('teacher', err.message || 'Network error. Is the server running?', true);
    } finally {
      sendBtn.disabled = false;
      inputEl.focus();
    }
  }

  sendBtn.addEventListener('click', send);
  if (newChatBtn) newChatBtn.addEventListener('click', startNewChat);

  inputEl.addEventListener('keydown', function (e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  });

  inputEl.addEventListener('input', function () {
    this.style.height = 'auto';
    this.style.height = Math.min(this.scrollHeight, 200) + 'px';
  });

  if (sidebarToggle && sidebar) {
    sidebarToggle.addEventListener('click', function () {
      sidebar.classList.toggle('open');
    });
  }

  renderChatList();
  showCurrentChat();

  fetch('/api/status')
    .then(function (r) { return r.json(); })
    .then(function (d) {
      if (backendBadge && d.backend) backendBadge.textContent = d.backend;
      if (backendBadge && d.error) backendBadge.textContent = 'Error';
    })
    .catch(function () {
      if (backendBadge) backendBadge.textContent = '—';
    });
})();
