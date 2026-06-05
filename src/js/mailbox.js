const API = {
  messages: "api/public/mailbox/list.php",
  mark: "api/public/mailbox/mark.php",
  maintenanceCheck: "api/public/maintenance/run-check.php"
};

document.addEventListener("DOMContentLoaded", async () => {
  startUtcClock();

  document.querySelector("#refreshButton")?.addEventListener("click", loadMessages);

  document.querySelector("#runMaintenanceCheckButton")?.addEventListener("click", async () => {
    try {
      const result = await postJson(API.maintenanceCheck, {});
      alert(`Maintenance check completed. Messages created: ${result.created_count}`);
      await loadMessages();
    } catch (error) {
      showError(error.message || "Unable to run maintenance check.");
    }
  });

  await loadMessages();
});

async function loadMessages() {
  hideError();

  try {
    const rows = await getJson(API.messages);
    renderMessages(rows);
  } catch (error) {
    showError(error.message || "Unable to load mailbox.");
  }
}

function renderMessages(rows) {
  const list = document.querySelector("#messageList");

  if (!rows.length) {
    list.innerHTML = `<p class="muted">No messages yet.</p>`;
    return;
  }

  list.innerHTML = rows.map(message => `
    <article class="message-card ${message.status === "UNREAD" ? "unread" : ""} ${message.severity.toLowerCase()}">
      <h3>${escapeHtml(message.title)}</h3>
      <div class="message-meta">
        <span class="badge ${message.severity.toLowerCase()}">${escapeHtml(message.severity)}</span>
        <span class="badge">${escapeHtml(message.message_type)}</span>
        <span class="badge">${escapeHtml(message.status)}</span>
        <span class="badge">${escapeHtml(message.created_at_utc)}</span>
      </div>
      <p>${escapeHtml(message.body)}</p>
      <div class="message-actions">
        ${message.status === "UNREAD" ? `<button type="button" data-action="READ" data-message-id="${message.message_id}">Mark read</button>` : ""}
        ${message.status !== "RESOLVED" ? `<button type="button" data-action="RESOLVE" data-message-id="${message.message_id}">Resolve</button>` : ""}
        ${message.status !== "ARCHIVED" ? `<button type="button" data-action="ARCHIVE" data-message-id="${message.message_id}">Archive</button>` : ""}
      </div>
    </article>
  `).join("");

  list.querySelectorAll("[data-message-id]").forEach(button => {
    button.addEventListener("click", async () => {
      try {
        await postJson(API.mark, {
          message_id: Number(button.dataset.messageId),
          action: button.dataset.action
        });
        await loadMessages();
      } catch (error) {
        showError(error.message || "Unable to update message.");
      }
    });
  });
}

async function getJson(url) {
  const response = await fetch(url, {
    headers: { "Accept": "application/json" },
    credentials: "same-origin"
  });

  const body = await response.json().catch(() => null);

  if (!response.ok) {
    throw new Error(body?.message || body?.error || `Request failed: ${response.status}`);
  }

  return body;
}

async function postJson(url, payload) {
  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Accept": "application/json",
      "Content-Type": "application/json"
    },
    credentials: "same-origin",
    body: JSON.stringify(payload)
  });

  const body = await response.json().catch(() => null);

  if (!response.ok) {
    throw new Error(body?.message || body?.error || `Request failed: ${response.status}`);
  }

  return body;
}

function startUtcClock() {
  const clock = document.querySelector("#utcClock");

  function tick() {
    const now = new Date();
    clock.textContent = now.toISOString().replace("T", " ").slice(0, 19) + " UTC";
  }

  tick();
  setInterval(tick, 1000);
}

function showError(message) {
  const error = document.querySelector("#pageError");
  error.hidden = false;
  error.textContent = message;
}

function hideError() {
  const error = document.querySelector("#pageError");
  error.hidden = true;
  error.textContent = "";
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}
