let isLoopRunning = false;

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
  const codeBlocks = Array.from(document.querySelectorAll('pre code, pre'));
  for (let i = codeBlocks.length - 1; i >= 0; i--) {
    const text = codeBlocks[i].innerText.trim();
    if (text.includes('"actions"') && text.includes('"type"')) {
      return text;
    }
  }
  return null;
}

function waitForCompletionAndSend() {
  let checkCount = 0;
  const maxChecks = 120;

  const poll = setInterval(() => {
    checkCount++;
    const generating = isGenerating();

    if (!generating && checkCount > 4) {
      clearInterval(poll);
      setTimeout(() => {
        const rawJson = extractLatestJson();
        if (rawJson && isLoopRunning) {
          chrome.runtime.sendMessage({
            action: "EXECUTE_PAYLOAD",
            raw_text: rawJson
          });
        } else if (isLoopRunning) {
          console.warn("[Local Agent] JSON в ответе не найден.");
        }
      }, 800);
    }

    if (checkCount >= maxChecks) {
      clearInterval(poll);
      console.error("[Local Agent] Таймаут ожидания ответа Gemini.");
    }
  }, 1000);
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