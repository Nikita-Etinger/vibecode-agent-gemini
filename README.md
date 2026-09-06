# Vibecode Agent: Autonomous Zero-Click Local Framework

Автономный инженерный агент для выполнения системных задач, разработки и управления GUI на платформе Windows 11 (Python 3.10+, PyCharm).

---

## 1. Архитектура

- **FastAPI Core (`main.py`):** Локальный сервер-исполнитель (`http://127.0.0.1:5050`), принимающий структурированные команды JSON по протоколу Vibecode.
- **Двусторонний браузерный мост (Zero-Click Loop):**
  - `chrome_extension_gemini/` — интеграция кнопки «Агент» и перехват ответов для Gemini (`gemini.google.com`).
  - `chrome_extension_chatgpt/` — интеграция кнопки «Агент», поддержка неформатированного JSON и автоотправка для ChatGPT (`chatgpt.com`).
  - Работает на базе `MutationObserver` для предотвращения троттлинга таймеров Chromium в неактивных окнах.
- **Инструментарий (`tools/`):**
  - `hid_controller.py`: надежный ввод данных через системный буфер обмена (`paste`), клики мышью, эмуляция хоткеев и фиксация окон поверх всех (`pin_window` через WinAPI `HWND_TOPMOST`).
  - `vision_ocr.py`: поиск элементов GUI и получение точных экранных координат через распознавание текста на экране.
- **Изоляция проектов (`workspace/`):** Рабочие файлы, пользовательские скрипты и артефакты задач сохраняются строго в изолированных папках внутри `workspace/`, не засоряя ядро агента.

---

## 2. Установка и запуск

### Запуск бэкенда:
```cmd
pip install -r requirements.txt
python main.py
```
Сервер доступен по адресу `http://127.0.0.1:5050`.

### Подключение браузерных расширений:
1. Перейдите в `chrome://extensions` и включите **«Режим разработчика»**.
2. Нажмите **«Загрузить распакованное расширение»**.
3. Выберите папку целевого расширения (`chrome_extension_gemini` или `chrome_extension_chatgpt`).

---

## 3. Протокол взаимодействия

Ответы моделей формируются строго внутри блока кода Markdown: ````json ... ````.

```json
{
  "summary": "Описание действий",
  "actions": [
    { "type": "create", "path": "workspace/app.py", "content": "..." },
    { "type": "patch", "path": "workspace/app.py", "search": "old", "replace": "new" },
    { "type": "command", "cmd": "python workspace/app.py", "report": true },
    { "type": "tool", "name": "hid_controller.pin_window", "args": { "window_title": "Chrome" } }
  ]
}
```
