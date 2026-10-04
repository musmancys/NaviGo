/**
 * NaviGo AI Chat Assistant Controller
 * Provides grounded tool-calling responses, rich cards, markdown rendering, and voice input.
 */

let chatHistory = [];

async function sendMessage() {
  const input = document.getElementById('chatInput');
  if (!input) return;
  const text = input.value.trim();
  if (!text) return;

  const messagesContainer = document.getElementById('chatMessages');
  if (!messagesContainer) return;

  // Append user message
  const userMsgHtml = `
    <div class="msg user">
      <div class="msg-bubble">${api.sanitize(text)}</div>
    </div>
  `;
  messagesContainer.insertAdjacentHTML('beforeend', userMsgHtml);
  input.value = '';
  messagesContainer.scrollTop = messagesContainer.scrollHeight;

  // Typing indicator
  const typingId = `typing-${Date.now()}`;
  messagesContainer.insertAdjacentHTML('beforeend', `
    <div class="msg ai" id="${typingId}">
      <div class="msg-bubble" style="color:var(--muted);">NaviGo is typing…</div>
    </div>
  `);
  messagesContainer.scrollTop = messagesContainer.scrollHeight;

  try {
    // Only pass destination if user is currently viewing a specific destination page
    const activeDest = state.currentDestination?.slug || null;
    const res = await api.post('/chat', {
      message: text,
      destination_slug: activeDest,
      history: chatHistory
    });

    const typingEl = document.getElementById(typingId);
    if (typingEl) typingEl.remove();

    // Render formatted markdown
    let formattedText = res.text;
    if (window.marked) {
      formattedText = window.marked.parse(res.text);
    }
    const sanitizedText = api.sanitize(formattedText);

    // Cards HTML
    let cardsHtml = '';
    if (res.cards && res.cards.length > 0) {
      cardsHtml = `
        <div class="msg-cards">
          ${res.cards.map(c => `
            <div class="msg-card">
              <div class="emoji">${c.emoji || '🏔️'}</div>
              <strong>${api.sanitize(c.title)}</strong>
              <small>${api.sanitize(c.subtitle)}</small>
            </div>
          `).join('')}
        </div>
      `;
    }

    const aiMsgHtml = `
      <div class="msg ai">
        <div class="msg-bubble">
          <div>${sanitizedText}</div>
          ${cardsHtml}
        </div>
      </div>
    `;

    messagesContainer.insertAdjacentHTML('beforeend', aiMsgHtml);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;

    // Save to history
    chatHistory.push({ role: 'user', content: text });
    chatHistory.push({ role: 'assistant', content: res.text });
  } catch (err) {
    console.error("Chat error:", err);
    const typingEl = document.getElementById(typingId);
    if (typingEl) typingEl.remove();
    messagesContainer.insertAdjacentHTML('beforeend', `
      <div class="msg ai">
        <div class="msg-bubble" style="color:var(--red);">Sorry, I encountered an issue. Please try again.</div>
      </div>
    `);
  }
}
window.sendMessage = sendMessage;

function askAI(topic) {
  const input = document.getElementById('chatInput');
  if (!input) return;

  const destName = state.currentDestination?.name;
  if (destName) {
    if (topic === 'Best places') {
      input.value = `What are the best places to visit in ${destName}?`;
    } else if (topic === 'Budget options') {
      input.value = `What are the best budget hotel and transport options for ${destName}?`;
    } else if (topic === 'Tomorrow plan') {
      input.value = `Plan a 1-day itinerary for tomorrow in ${destName}.`;
    } else if (topic === 'Weather') {
      input.value = `What is the current weather and road condition in ${destName}?`;
    } else {
      input.value = topic;
    }
  } else {
    // No specific destination selected — ask across Pakistan
    if (topic === 'Best places') {
      input.value = 'What are the best tourist places to visit across Pakistan?';
    } else if (topic === 'Budget options') {
      input.value = 'Suggest budget-friendly travel destinations in Pakistan under Rs. 50,000.';
    } else if (topic === 'Tomorrow plan') {
      input.value = 'How should I plan a 3-day weekend trip in Pakistan?';
    } else if (topic === 'Weather') {
      input.value = 'Which destinations in Pakistan have good weather to visit right now?';
    } else {
      input.value = topic;
    }
  }
  sendMessage();
}
window.askAI = askAI;
