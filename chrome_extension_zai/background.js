const ICON_DATA = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==";

let loopState = {
  active: false,
  retries: 0,
  maxRetries: 5,
  tabId: null
};

chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: "start_agent_loop_zai",
    title: "Запустить Zero-Click Loop (Z.AI)",
    contexts: ["selection"]
  });
});

chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === "start_agent_loop_zai" && info.selectionText) {
    loopState.active = true;
    loopState.retries = 0;
    loopState.tabId = tab ? tab.id : null;
    executeWithAgent(info.selectionText);
  }
});

chrome.runtime.onMessage.addListener((msg, sender) => {
  if (msg.action === "EXECUTE_PAYLOAD") {
    loopState.active = true;
    loopState.retries = 0;
    loopState.tabId = sender.tab ? sender.tab.id : loopState.tabId;
    executeWithAgent(msg.raw_text);
  }
});

async function executeWithAgent(rawText) {
  try {
    const response = await fetch("http://127.0.0.1:5050/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ raw_text: rawText })
    });

    const result = await response.json();

    if (result.success) {
      loopState.active = false;
      chrome.notifications.create({
        type: "basic",
        iconUrl: ICON_DATA,
        title: "Zero-Click (Z.AI): Успех!",
        message: "Все операции и тесты выполнены успешно."
      });
      if (loopState.tabId) {
        chrome.tabs.sendMessage(loopState.tabId, { action: "STOP_LOOP" });
      }
    } else {
      if (loopState.retries >= loopState.maxRetries) {
        loopState.active = false;
        chrome.notifications.create({
          type: "basic",
          iconUrl: ICON_DATA,
          title: "Zero-Click (Z.AI): Превышен лимит",
          message: "Достигнут максимум итераций (5). Требуется ручной разбор."
        });
        return;
      }

      loopState.retries++;
      chrome.notifications.create({
        type: "basic",
        iconUrl: ICON_DATA,
        title: `Zero-Click (Z.AI): Ошибка (${loopState.retries}/5)`,
        message: "Промпт с ошибкой отправляется в чат..."
      });

      if (loopState.tabId && result.prompt) {
        chrome.tabs.sendMessage(loopState.tabId, {
          action: "INJECT_AND_SUBMIT",
          prompt: result.prompt
        });
      }
    }
  } catch (err) {
    loopState.active = false;
    chrome.notifications.create({
      type: "basic",
      iconUrl: ICON_DATA,
      title: "Ошибка подключения",
      message: "Локальный агент 127.0.0.1:5050 недоступен."
    });
  }
}
