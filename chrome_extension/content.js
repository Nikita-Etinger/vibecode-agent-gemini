(() => {
  console.log('[Vibecode Agent] content.js инициализирован (Event Delegation mode)');

  function updateButtonAppearance(wrapper) {
    if (wrapper.dataset.agentDecorated === 'true') return;
    wrapper.dataset.agentDecorated = 'true';

    wrapper.setAttribute('arialabel', 'Отправить агенту');
    wrapper.setAttribute('gemtooltip', 'Отправить агенту');

    const btn = wrapper.querySelector('button') || wrapper;
    btn.setAttribute('aria-label', 'Отправить агенту');
    btn.title = 'Отправить агенту';

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

  // Глобальное делегирование: перехват клика строго в момент нажатия
  document.addEventListener('click', (e) => {
    const target = e.target;
    const trigger = target.closest('.download-button, [fonticonname="arrow_circle_down"], [arialabel="Скачать код"], [arialabel="Отправить агенту"], [gemtooltip="Скачать код"], [gemtooltip="Отправить агенту"]');
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

  function setInputValue(element, text) {
    element.focus();
    document.execCommand('selectAll', false, null);
    document.execCommand('insertText', false, text);
    element.dispatchEvent(new Event('input', { bubbles: true }));
  }

  chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
    if (msg.action === 'INJECT_AND_SUBMIT' || msg.action === 'inject_prompt') {
      const inputField = findGeminiInput();
      if (!inputField) return;

      setInputValue(inputField, msg.prompt);

      setTimeout(() => {
        const btn = findSendButton();
        if (btn && !btn.disabled) {
          btn.click();
        }
      }, 500);
    }
  });

  const observer = new MutationObserver(() => {
    decorateAllButtons();
  });
  if (document.body) {
    observer.observe(document.body, { childList: true, subtree: true });
  }
  decorateAllButtons();
})();