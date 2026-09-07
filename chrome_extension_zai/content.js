let isLoopRunning = false;

function extractCodeFromBlock(blockContainer) {
  const cmContent = blockContainer.querySelector('.cm-content');
  if (cmContent) {
    const lines = Array.from(cmContent.querySelectorAll('.cm-line'));
    if (lines.length > 0) {
      return lines.map((line) => line.textContent).join('\n').trim();
    }
    return cmContent.innerText.trim();
  }

  const codeElem = blockContainer.querySelector('pre code, pre, textarea');
  return codeElem ? codeElem.innerText.trim() : '';
}

function injectAgentButtons() {
  const copyContainers = document.querySelectorAll('.copy-code-button, [aria-label="Copy"], div[id^="bits-"][aria-label="Copy"]');

  copyContainers.forEach((targetElem) => {
    const triggerWrapper = targetElem.closest('[aria-label="Copy"]') || targetElem;
    const parentGroup = triggerWrapper.parentElement;
    if (!parentGroup || parentGroup.dataset.agentInjected === 'true') return;
    parentGroup.dataset.agentInjected = 'true';

    const agentBtn = document.createElement('button');
    agentBtn.type = 'button';
    agentBtn.className = 'p-1.5 bg-none rounded-md border-none transition hover:bg-gray-100 dark:hover:bg-gray-800';
    agentBtn.setAttribute('aria-label', 'Агент');
    agentBtn.title = 'Выполнить код агентом';
    agentBtn.style.color = '#7287fd';
    agentBtn.style.cursor = 'pointer';
    agentBtn.style.display = 'inline-flex';
    agentBtn.style.alignItems = 'center';
    agentBtn.style.justifyContent = 'center';

    agentBtn.innerHTML = `
      <svg viewBox="0 0 20 20" fill="currentColor" class="size-4" style="display:block;">
        <path d="M6.3 2.841A1.5 1.5 0 004 4.11V15.89a1.5 1.5 0 002.3 1.269l9.344-5.89a1.5 1.5 0 000-2.538L6.3 2.84z"/>
      </svg>
    `;

    agentBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      e.preventDefault();

      const blockContainer = parentGroup.closest('.relative.my-2') || parentGroup.closest('[dir="ltr"]');
      if (!blockContainer) return;

      const rawCode = extractCodeFromBlock(blockContainer);
      if (!rawCode) {
        console.warn('[Z.AI Agent] Код не найден в блоке редактора');
        return;
      }

      agentBtn.style.transform = 'scale(0.85)';
      setTimeout(() => { agentBtn.style.transform = 'none'; }, 150);

      chrome.runtime.sendMessage({ action: 'EXECUTE_PAYLOAD', raw_text: rawCode });
    });

    parentGroup.insertBefore(agentBtn, triggerWrapper);
  });
}

function findZaiInput() {
  return document.querySelector('textarea#chat-input') || document.querySelector('textarea.input-scroll') || document.querySelector('textarea');
}

function findSendButton() {
  return document.querySelector('#send-message-button') || document.querySelector('button.sendMessageButton') || document.querySelector('button[type="submit"]');
}

function setInputValue(textarea, text) {
  textarea.focus();
  textarea.value = text;
  textarea.dispatchEvent(new Event('input', { bubbles: true }));
  textarea.dispatchEvent(new Event('change', { bubbles: true }));
}

function isGenerating() {
  const sendBtn = findSendButton();
  if (sendBtn && sendBtn.disabled && sendBtn.querySelector('svg.animate-spin')) return true;
  return !!document.querySelector('.animate-spin, [data-loading="true"]');
}

function waitForCompletionAndSend() {
  const checkInterval = setInterval(() => {
    if (isGenerating()) return;

    clearInterval(checkInterval);
    setTimeout(() => {
      const codeBlocks = Array.from(document.querySelectorAll('.relative.my-2'));
      for (let i = codeBlocks.length - 1; i >= 0; i--) {
        const block = codeBlocks[i];
        if (block.dataset.agentProcessed === 'true') continue;
        const text = extractCodeFromBlock(block);
        if (text.includes('"actions"') && text.includes('"type"')) {
          block.dataset.agentProcessed = 'true';
          chrome.runtime.sendMessage({ action: 'EXECUTE_PAYLOAD', raw_text: text });
          return;
        }
      }
    }, 800);
  }, 500);
}

chrome.runtime.onMessage.addListener((msg) => {
  if (msg.action === 'INJECT_AND_SUBMIT') {
    isLoopRunning = true;
    const inputEl = findZaiInput();
    if (!inputEl) {
      console.error('[Z.AI Agent] Поле ввода chat-input не найдено');
      return;
    }

    setInputValue(inputEl, msg.prompt);

    setTimeout(() => {
      const sendBtn = findSendButton();
      if (sendBtn && !sendBtn.disabled) {
        sendBtn.click();
        waitForCompletionAndSend();
      } else {
        inputEl.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true }));
        waitForCompletionAndSend();
      }
    }, 300);
  }

  if (msg.action === 'STOP_LOOP') {
    isLoopRunning = false;
  }
});

const observer = new MutationObserver(() => {
  injectAgentButtons();
});

observer.observe(document.body, { childList: true, subtree: true });
injectAgentButtons();
