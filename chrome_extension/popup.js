const toggle = document.getElementById('injectToggle');
const statusText = document.getElementById('statusText');

chrome.storage.local.get(['autoInjectEnabled'], (result) => {
  const isEnabled = result.autoInjectEnabled !== false;
  toggle.checked = isEnabled;
  statusText.textContent = isEnabled ? 'Статус: Авто-инжект ВКЛ' : 'Статус: Авто-инжект ВЫКЛ';
});

toggle.addEventListener('change', () => {
  const isEnabled = toggle.checked;
  chrome.storage.local.set({ autoInjectEnabled: isEnabled }, () => {
    statusText.textContent = isEnabled ? 'Статус: Авто-инжект ВКЛ' : 'Статус: Авто-инжект ВЫКЛ';
  });
});