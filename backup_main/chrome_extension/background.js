async function logToAgent(message, level = "INFO") {
  console.log(`[AgentLog:${level}]`, message);
  try {
    await fetch("http://127.0.0.1:5050/log", {
      method: "POST",
      headers: { "Content-Type": "application/json; charset=utf-8" },
      body: JSON.stringify({ message, level })
    });
  } catch (e) {}
}

self.addEventListener("unhandledrejection", (event) => {
  const reason = event.reason ? (event.reason.stack || event.reason.message || String(event.reason)) : "Unknown rejection";
  logToAgent("Unhandled Rejection: " + reason, "ERROR");
  event.preventDefault();
});

self.addEventListener("error", (event) => {
  const errText = `${event.message} at ${event.filename}:${event.lineno}:${event.colno}`;
  logToAgent("Global Error: " + errText, "ERROR");
});

chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: "run-zero-click",
    title: "Запустить Zero-Click Loop",
    contexts: ["selection"]
  });
});

let retryCount = 0;
const MAX_RETRIES = 10;

chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === "run-zero-click") {
    retryCount = 0;
    executeAgent(info.selectionText, tab.id);
  }
});

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === "EXECUTE_PAYLOAD" || message.action === "loop_next") {
    const text = message.raw_text || message.payload;
    const tabId = sender.tab ? sender.tab.id : null;
    executeAgent(text, tabId);
  }
});

async function sendPromptToTab(tabId, promptText) {
  const payload = { action: "INJECT_AND_SUBMIT", prompt: promptText };
  if (tabId) {
    try {
      await chrome.tabs.sendMessage(tabId, payload);
      return;
    } catch (e) {
      logToAgent(`Вкладка ${tabId} недоступна: ${e.message}`, "WARN");
    }
  }
  try {
    const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
    for (const tab of tabs) {
      if (tab.id) {
        try {
          await chrome.tabs.sendMessage(tab.id, payload);
          return;
        } catch (err) {}
      }
    }
  } catch (err) {
    logToAgent(`Ошибка поиска активной вкладки: ${err.message}`, "ERROR");
  }
}

function extractAgentPayload(rawText) {
  if (!rawText) return null;
  const text = rawText.trim();

  // 1. Проверка сырого текста как JSON
  try {
    const parsed = JSON.parse(text);
    if (parsed && typeof parsed === "object" && (parsed.actions || parsed.summary)) {
      return JSON.stringify(parsed);
    }
  } catch (e) {}

  // 2. Итеративный поиск по всем кодовым блокам
  const codeBlockRegex = /```(?:json)?\s*([\s\S]*?)\s*```/g;
  let match;
  while ((match = codeBlockRegex.exec(text)) !== null) {
    const candidate = match[1].trim();
    try {
      const parsed = JSON.parse(candidate);
      if (parsed && typeof parsed === "object" && (parsed.actions || parsed.summary)) {
        return JSON.stringify(parsed);
      }
    } catch (e) {}
  }

  // 3. Fallback: поиск по внешним фигурным скобкам
  const firstBrace = text.indexOf("{");
  const lastBrace = text.lastIndexOf("}");
  if (firstBrace !== -1 && lastBrace > firstBrace) {
    const candidate = text.slice(firstBrace, lastBrace + 1).trim();
    try {
      const parsed = JSON.parse(candidate);
      if (parsed && typeof parsed === "object" && (parsed.actions || parsed.summary)) {
        return JSON.stringify(parsed);
      }
    } catch (e) {}
  }

  return null;
}

async function executeAgent(rawText, tabId) {
  const payload = extractAgentPayload(rawText);
  if (!payload) {
    logToAgent("Пропуск: в сообщении не обнаружен валидный JSON-манифест агента", "DEBUG");
    return;
  }

  try {
    logToAgent("Отправка payload в агент...", "DEBUG");
    const response = await fetch("http://127.0.0.1:5050/execute", {
      method: "POST",
      headers: { "Content-Type": "application/json; charset=utf-8" },
      body: payload
    });
    const data = await response.json();

    if (data.prompt && (!data.success || data.needs_reply)) {
      await sendPromptToTab(tabId, data.prompt);
    }
  } catch (err) {
    logToAgent("executeAgent fetch сбой: " + (err.stack || err.message || err), "ERROR");
    console.error("Agent connection error:", err);
  }
}