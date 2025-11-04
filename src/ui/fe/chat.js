document.addEventListener("DOMContentLoaded", () => {
  sessionStorage.removeItem("fromConnect");
  const chatContainer = document.getElementById("chatContainer");
  const chatForm = document.getElementById("chatForm");
  const chatInput = document.getElementById("chatInput");
  const sendBtn = document.getElementById("sendBtn");
  const clearBtn = document.getElementById("clearBtn");

  const STORAGE_KEY = "chatHistory";
  let chatHistory = [];

  // Load chat
  try {
    chatHistory = JSON.parse(localStorage.getItem(STORAGE_KEY)) || [];
  } catch {
    chatHistory = [];
  }

  // Escape to prevent XSS
  const escapeHtml = s => s.replace(/[&<>"']/g, c => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  })[c] || c);
  
  // Render Markdown -> safe HTML. Also auto-embed plain image URLs or array-like image lists.
function renderMarkdownSafe(mdText) {
  if (!mdText && mdText !== 0) return "";
  let text = String(mdText);

  // Quick support for array-like image output: "['https://...png?']"
  // Convert patterns like ['url'] or ["url"] or [ 'url' ] into plain markdown image syntax
  text = text.replace(/\[\s*['"]?(https?:\/\/[^\]'"]+)['"]?\s*\]/g, (m, url) => {
    // use markdown image syntax for better placement with other text
    return `![](${url})`;
  });

  // Also convert naked URLs on their own line into markdown links/images
  text = text.replace(/(^|\n)(https?:\/\/\S+)(?=$|\n)/g, (m, p1, url) => {
    // If it ends with image extension, make it an image syntax
    if (/\.(png|jpg|jpeg|gif|webp|svg)(\?|$)/i.test(url)) return `${p1}![](${url})`;
    return `${p1}[${url}](${url})`;
  });

  // Use marked to parse markdown -> html
  const dirty = marked.parse(text, { gfm: true, breaks: true });
  // sanitize
  const clean = DOMPurify.sanitize(dirty, { SAFE_FOR_TEMPLATES: true });
  return clean;
}


const renderMessage = (msg) => {
  // msg may be { role, text, ts } or { role, tableData, ts }
  const { role, text, ts } = msg;
  const time = new Date(ts).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  const wrapper = document.createElement("div");

  // full-width container; align items within depending on role
  wrapper.className = "w-full flex flex-col " + (role === "user" ? "items-end" : "items-start");

  if (role === "user") {
    // user bubble (right)
    wrapper.innerHTML = `
      <div class="ml-auto bg-indigo-600 text-white px-4 py-2 rounded-2xl rounded-tr-sm shadow text-sm">${escapeHtml(text)}</div>
      <div class="ml-auto text-xs text-gray-400 mt-1">${time}</div>
    `;
    wrapper.classList.add("text-right");
    return wrapper;
  }

  // BOT branch
  // If tableData present, render a table
  if (msg.tableData && Array.isArray(msg.tableData) && msg.tableData.length > 0) {
    const cols = Object.keys(msg.tableData[0]);
    const thead = `<tr>${cols.map(c => `<th class="px-3 py-2 text-left text-xs text-gray-500">${escapeHtml(c)}</th>`).join("")}</tr>`;
    const tbody = msg.tableData.map(row => {
      return `<tr class="odd:bg-white even:bg-gray-50">${cols.map(c => {
        const cellVal = row[c] === null || row[c] === undefined ? "" : String(row[c]);
        return `<td class="px-3 py-2 align-top text-sm text-gray-700">${escapeHtml(cellVal)}</td>`;
      }).join("")}</tr>`;
    }).join("");

    wrapper.innerHTML = `
      <div class="mr-auto text-left">
        <div class="overflow-auto rounded-lg border border-gray-200 bg-white shadow-sm">
          <table class="min-w-full text-left">
            <thead class="bg-gray-100">${thead}</thead>
            <tbody>${tbody}</tbody>
          </table>
        </div>
        <div class="text-xs text-gray-400 mt-1">${time}</div>
      </div>
    `;
    return wrapper;
  }

  // fallback: regular bot text bubble
    const rendered = renderMarkdownSafe(text || "");
    wrapper.innerHTML = `
    <div class="mr-auto bg-gray-100 px-4 py-2 rounded-2xl rounded-tl-sm text-sm">
        <div class="prose max-w-none">${rendered}</div>
    </div>
    <div class="mr-auto text-xs text-gray-400 mt-1">${time}</div>
    `;

  wrapper.classList.add("text-left");
  return wrapper;
};


  const renderChat = () => {
    chatContainer.innerHTML = "";
    for (const msg of chatHistory) chatContainer.appendChild(renderMessage(msg));
    chatContainer.scrollTo({ top: chatContainer.scrollHeight, behavior: "smooth" });
  };

  const persist = () => localStorage.setItem(STORAGE_KEY, JSON.stringify(chatHistory));

async function echoResponse(userText) {
  // Show a typing indicator
  const typing = { role: "bot", text: "Typing...", ts: Date.now(), temp: true };
  chatHistory.push(typing);
  renderChat();

  // Build payload: prefer CSV url if present, otherwise DB connection if present
  const payload = { query: userText };

  try {
// pick the most recently saved source (csv or db)
// support older plain-string keys too for backward compatibility
    function readMeta(key, fallbackKey) {
    const metaRaw = localStorage.getItem(key);
    if (metaRaw) {
        try { return JSON.parse(metaRaw); } catch { /* ignore */ }
    }
    // fallback to legacy plain string
    const legacy = localStorage.getItem(fallbackKey);
    return legacy ? { value: legacy, savedAt: 0 } : null;
    }

    const csvMeta = readMeta("uploadedCsvMeta", "uploadedCsvUrl");
    const dbMeta  = readMeta("savedDbConnMeta", "savedDbConn");

    if (csvMeta && dbMeta) {
    // pick latest
    if ((csvMeta.savedAt || 0) >= (dbMeta.savedAt || 0)) {
        payload.csv_url = csvMeta.value;
    } else {
        payload.db_url = dbMeta.value;
    }
    } else if (csvMeta) {
    payload.csv_url = csvMeta.value;
    } else if (dbMeta) {
    payload.db_url = dbMeta.value;
    }

    // POST to your API. Change host/port if needed.
    const resp = await axios.post("http://127.0.0.1:8000/query", payload, { timeout: 900000 });

    // Remove typing indicator
    chatHistory = chatHistory.filter(m => !m.temp);

    // Get data safely
    const data = resp && resp.data ? resp.data : {};

    // If API returned an array of objects in data.message, show it as a table
    if (Array.isArray(data.message) && data.message.length > 0 && typeof data.message[0] === "object") {
      chatHistory.push({ role: "bot", tableData: data.message, ts: Date.now() });
    } else {
      const botText = (typeof data === "string") ? data : (data.message || data.reply || data.text || JSON.stringify(data));
      chatHistory.push({ role: "bot", text: String(botText), ts: Date.now() });
    }

    persist();
    renderChat();

  } catch (err) {
    console.error("Query error:", err);

    // Remove typing indicator
    chatHistory = chatHistory.filter(m => !m.temp);

    // Friendly error message for the chat
    const errMsg = err.response && err.response.data
      ? (err.response.data.message || JSON.stringify(err.response.data))
      : (err.message || "Unknown error");

    chatHistory.push({ role: "bot", text: `Error: ${errMsg}`, ts: Date.now() });
    persist();
    renderChat();
  }
}


  chatForm.addEventListener("submit", e => {
    e.preventDefault();
    const text = chatInput.value.trim();
    if (!text) return;
    chatHistory.push({ role: "user", text, ts: Date.now() });
    chatInput.value = "";
    persist();
    renderChat();
    echoResponse(text);
  });

  chatInput.addEventListener("keydown", e => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendBtn.click();
    }
  });

  clearBtn.addEventListener("click", () => {
    if (!confirm("Clear chat history?")) return;
    chatHistory = [];
    persist();
    renderChat();
  });

  renderChat();
});
