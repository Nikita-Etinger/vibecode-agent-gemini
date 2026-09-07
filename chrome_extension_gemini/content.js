let isLoopRunning = false;
let lastExecutedPayload = "";

  function updateButtonAppearance(wrapper) {
    if (wrapper.dataset.agentDecorated === 'true') return;
    wrapper.dataset.agentDecorated = 'true';

    wrapper.setAttribute('arialabel', 'Агент');
    wrapper.setAttribute('gemtooltip', 'Агент');

    const btn = wrapper.querySelector('button') || wrapper;
    btn.setAttribute('aria-label', 'Агент');
    btn.title = 'Агент';

    const icon = wrapper.querySelector('mat-icon');
    if (icon) {
      icon.innerHTML = `<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" style="display:block;"><path d="M8 5v14l11-7z"/></svg>`;
      icon.style.color = '#a594fd';
    }
  }

  function decorateAllButtons() {
    const downloadContainers = document.querySelectorAll('.download-button, [fonticonname="arrow_circle_down"], [arialabel="Скачать код"], [gemtooltip="Скачать код"]');
    downloadContainers.forEach(updateButtonAppearance);
  }

  document.addEventListener('click', (e) => {
    const target = e.target;
    const trigger = target.closest('.download-button, [fonticonname="arrow_circle_down"], [arialabel="Скачать код"], [arialabel="Агент"], [gemtooltip="Скачать код"], [gemtooltip="Агент"]');
    if (!trigger) return;

    e.stopImmediatePropagation();
    e.stopPropagation();
    e.preventDefault();

    const hostBlock = trigger.closest('code-block') || trigger.closest('.formatted-code-block-internal-container');
    if (!hostBlock) return;

    const codeElem = hostBlock.querySelector("pre code[data-test-id='code-content']") || hostBlock.querySelector('pre code') || hostBlock.querySelector('pre');
    const rawCode = codeElem ? codeElem.innerText.trim() : '';
    if (!rawCode) return;

    const btn = trigger.querySelector('button') || trigger;
    btn.style.transform = 'scale(0.85)';
    setTimeout(() => { btn.style.transform = 'none'; }, 150);

    chrome.runtime.sendMessage({ action: 'EXECUTE_PAYLOAD', raw_text: rawCode });
  }, true);

function findGeminiInput() {
  return (
    document.querySelector('rich-textarea div[contenteditable="true"]') ||
    document.querySelector('div[contenteditable="true"][role="textbox"]') ||
    document.querySelector('div.ql-editor') ||
    document.querySelector('textarea')
  );
}

function findSendButton() {
  return (
    document.querySelector('button[aria-label*="Отправить"]') ||
    document.querySelector('button[aria-label*="Send"]') ||
    document.querySelector('button.send-button') ||
    document.querySelector('.send-button-container button')
  );
}

function isGenerating() {
  return !!(
    document.querySelector('button[aria-label*="Остановить"]') ||
    document.querySelector('button[aria-label*="Stop"]') ||
    document.querySelector('mat-progress-bar') ||
    document.querySelector('.generating')
  );
}

function setInputValue(element, text) {
  element.focus();
  document.execCommand('selectAll', false, null);
  document.execCommand('insertText', false, text);
  element.dispatchEvent(new Event('input', { bubbles: true }));
}

function extractLatestJson() {
  const responses = document.querySelectorAll('model-response, .model-response, [data-test-id="model-response"]');
  const targetScope = responses.length > 0 ? responses[responses.length - 1] : document;
  const codeBlocks = Array.from(targetScope.querySelectorAll('pre code, pre'));

  for (let i = codeBlocks.length - 1; i >= 0; i--) {
    const block = codeBlocks[i];
    if (block.dataset.agentProcessed === 'true') continue;
    const text = block.innerText.trim();
    if (text.includes('"actions"') && text.includes('"type"')) {
      block.dataset.agentProcessed = 'true';
      return text;
    }
  }
  return null;
}

let activeResponseObserver = null;

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
          console.log("[Local Agent] Повторный JSON отфильтрован в расширении.");
          return;
        }
        lastExecutedPayload = rawJson;
        chrome.runtime.sendMessage({
          action: "EXECUTE_PAYLOAD",
          raw_text: rawJson
        });
      } else if (isLoopRunning) {
        console.log("[Local Agent] Модель вернула текстовый ответ. Цикл ожидания завершен без действий.");
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
    const inputField = findGeminiInput();
    if (!inputField) {
      console.error("[Local Agent] Поле ввода Gemini не найдено.");
      return;
    }

    setInputValue(inputField, msg.prompt);

    setTimeout(() => {
      const btn = findSendButton();
      if (btn && !btn.disabled) {
        btn.click();
        setTimeout(waitForCompletionAndSend, 1500);
      } else {
        console.error("[Local Agent] Кнопка отправки не найдена или неактивна.");
      }
    }, 600);
  }

  if (msg.action === "STOP_LOOP") {
    isLoopRunning = false;
  }
});

const observer = new MutationObserver(() => {
  decorateAllButtons();
});
if (document.body) {
  observer.observe(document.body, { childList: true, subtree: true });
}
decorateAllButtons();