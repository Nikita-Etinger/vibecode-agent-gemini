let isLoopRunning = false;
let lastExecutedPayload = "";
let activeResponseObserver = null;

function extractJsonFromText(raw) {
  if (!raw) return null;
  const startIdx = raw.indexOf('{');
  const endIdx = raw.lastIndexOf('}');
  if (startIdx === -1 || endIdx === -1 || endIdx <= startIdx) return null;
  const candidate = raw.slice(startIdx, endIdx + 1).trim();
  if (candidate.includes('"actions"') && (candidate.includes('"type"') || candidate.includes('"summary"'))) {
    return candidate;
  }
  return null;
}

function injectAgentButtons() {
  const copyButtons = document.querySelectorAll('button[aria-label="Копировать"], button[aria-label="Copy"]');

  copyButtons.forEach((copyBtn) => {
    const buttonContainer = copyBtn.parentElement;
    if (!buttonContainer || buttonContainer.dataset.agentInjected === "true") return;
    buttonContainer.dataset.agentInjected = "true";

    const agentBtn = document.createElement("button");
    agentBtn.type = "button";
    agentBtn.className = copyBtn.className;
    agentBtn.setAttribute("aria-label", "Агент");
    agentBtn.title = "Выполнить код агентом";
    agentBtn.style.color = "#10a37f";
    agentBtn.style.cursor = "pointer";

    agentBtn.innerHTML = `
      <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="currentColor" class="icon-md">
        <path d="M8 5v14l11-7z"/>
      </svg>
    `;

    agentBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      e.preventDefault();

      const codeContainer = buttonContainer.closest("pre") || buttonContainer.closest("div.relative") || buttonContainer.parentElement.parentElement;
      const codeElement = codeContainer ? codeContainer.querySelector("code") : null;
      const rawCode = codeElement ? codeElement.innerText.trim() : "";

      if (!rawCode) {
        console.warn("[ChatGPT Agent] Текст кода не найден.");
        return;
      }

      agentBtn.style.transform = "scale(0.85)";
      setTimeout(() => { agentBtn.style.transform = "none"; }, 150);

      chrome.runtime.sendMessage({ action: "EXECUTE_PAYLOAD", raw_text: rawCode });
    });

    buttonContainer.insertBefore(agentBtn, copyBtn);
  });

  const messages = document.querySelectorAll('[data-message-author-role="assistant"], article');
  messages.forEach((msg) => {
    if (msg.querySelector('pre code')) return;
    if (msg.dataset.agentTextChecked === "true") return;
    
    const rawText = msg.innerText || "";
    const validJson = extractJsonFromText(rawText);
    if (!validJson) return;

    msg.dataset.agentTextChecked = "true";
    msg.style.position = "relative";

    const floatBtn = document.createElement("button");
    floatBtn.type = "button";
    floatBtn.innerText = "▶ Запустить Агент";
    floatBtn.style.position = "absolute";
    floatBtn.style.top = "8px";
    floatBtn.style.right = "8px";
    floatBtn.style.zIndex = "50";
    floatBtn.style.padding = "6px 12px";
    floatBtn.style.fontSize = "12px";
    floatBtn.style.fontWeight = "600";
    floatBtn.style.color = "#ffffff";
    floatBtn.style.backgroundColor = "#10a37f";
    floatBtn.style.border = "none";
    floatBtn.style.borderRadius = "6px";
    floatBtn.style.cursor = "pointer";
    floatBtn.style.boxShadow = "0 2px 5px rgba(0,0,0,0.2)";

    floatBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      e.preventDefault();
      floatBtn.style.transform = "scale(0.9)";
      setTimeout(() => { floatBtn.style.transform = "none"; }, 150);
      chrome.runtime.sendMessage({ action: "EXECUTE_PAYLOAD", raw_text: validJson });
    });

    msg.appendChild(floatBtn);
  });
}

function findChatGPTInput() {
  return (
    document.querySelector("#prompt-textarea") ||
    document.querySelector('div[contenteditable="true"][id="prompt-textarea"]') ||
    document.querySelector('div[contenteditable="true"][role="textbox"]') ||
    document.querySelector("textarea[data-id=\"root\"]") ||
    document.querySelector("textarea")
  );
}

function findSendButton() {
  return (
    document.querySelector('button[data-testid="send-button"]') ||
    document.querySelector('button[aria-label="Отправить подсказку"]') ||
    document.querySelector('button[aria-label="Send prompt"]') ||
    document.querySelector('form button[type="submit"]')
  );
}

function isGenerating() {
  return !!(
    document.querySelector('button[data-testid="stop-button"]') ||
    document.querySelector('button[aria-label="Остановить генерацию"]') ||
    document.querySelector('button[aria-label="Stop generating"]') ||
    document.querySelector('.result-streaming')
  );
}

function setInputValue(element, text) {
  element.focus();
  if (element.tagName.toLowerCase() === "textarea") {
    element.value = text;
    element.dispatchEvent(new Event("input", { bubbles: true }));
  } else {
    document.execCommand("selectAll", false, null);
    document.execCommand("insertText", false, text);
    element.dispatchEvent(new Event("input", { bubbles: true }));
  }
}

function extractLatestJson() {
  const messageContainers = document.querySelectorAll('[data-message-author-role="assistant"], article');
  const targetScope = messageContainers.length > 0 ? messageContainers[messageContainers.length - 1] : document;
  const codeBlocks = Array.from(targetScope.querySelectorAll("pre code, pre"));

  for (let i = codeBlocks.length - 1; i >= 0; i--) {
    const block = codeBlocks[i];
    if (block.dataset.agentProcessed === "true") continue;
    const text = block.innerText.trim();
    if (text.includes('"actions"') && text.includes('"type"')) {
      block.dataset.agentProcessed = "true";
      return text;
    }
  }

  if (targetScope && targetScope.dataset.agentProcessed !== "true") {
    const plainText = targetScope.innerText || "";
    const fallbackJson = extractJsonFromText(plainText);
    if (fallbackJson) {
      targetScope.dataset.agentProcessed = "true";
      return fallbackJson;
    }
  }

  return null;
}

function waitForCompletionAndSend() {
  if (activeResponseObserver) {
    activeResponseObserver.disconnect();
    activeResponseObserver = null;
  }

  const triggerCompletion = () => {
    if (activeResponseObserver) {
      activeResponseObserver.disconnect();
      activeResponseObserver = null;
    }
    setTimeout(() => {
      const rawJson = extractLatestJson();
      if (rawJson && isLoopRunning) {
        if (rawJson === lastExecutedPayload) {
          console.log("[ChatGPT Agent] Повторный JSON отфильтрован в расширении.");
          return;
        }
        lastExecutedPayload = rawJson;
        chrome.runtime.sendMessage({
          action: "EXECUTE_PAYLOAD",
          raw_text: rawJson
        });
      } else if (isLoopRunning) {
        console.log("[ChatGPT Agent] Модель вернула текстовый ответ. Цикл завершен.");
        isLoopRunning = false;
      }
    }, 300);
  };

  let wasGeneratingSeen = false;

  activeResponseObserver = new MutationObserver(() => {
    const generating = isGenerating();
    if (generating) {
      wasGeneratingSeen = true;
    } else if (wasGeneratingSeen && !generating) {
      triggerCompletion();
    }
  });

  activeResponseObserver.observe(document.body, { childList: true, subtree: true, attributes: true });

  setTimeout(() => {
    if (activeResponseObserver && !isGenerating()) {
      triggerCompletion();
    }
  }, 4000);
}

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.action === "INJECT_AND_SUBMIT") {
    isLoopRunning = true;
    const inputField = findChatGPTInput();
    if (!inputField) {
      console.error("[ChatGPT Agent] Поле ввода не найдено.");
      return;
    }

    setInputValue(inputField, msg.prompt);

    setTimeout(() => {
      const btn = findSendButton();
      if (btn && !btn.disabled) {
        btn.click();
        setTimeout(waitForCompletionAndSend, 1500);
      } else {
        console.error("[ChatGPT Agent] Кнопка отправки не найдена или неактивна.");
      }
    }, 600);
  }

  if (msg.action === "STOP_LOOP") {
    isLoopRunning = false;
  }
});

const observer = new MutationObserver(() => {
  injectAgentButtons();
});

if (document.body) {
  observer.observe(document.body, { childList: true, subtree: true });
}
injectAgentButtons();
