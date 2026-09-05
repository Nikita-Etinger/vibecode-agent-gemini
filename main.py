import ast
import hashlib
import json
import os
import time
import re
import shutil
import site
import subprocess
import sys
import threading
import tkinter as tk
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from tkinter import scrolledtext

BG_MAIN = "#696969"
BG_INPUT = "#808080"
BTN_COLOR = "#6A5ACD"
BTN_SECONDARY = "#555555"
TEXT_COLOR = "#FFFFFF"
SERVER_PORT = 5050

BASE_DIR = Path(__file__).resolve().parent
BACKUP_DIR = BASE_DIR / "backups"
SCRIPTS_DIR = BASE_DIR / "scripts"
LOG_FILE = BASE_DIR / "main.log"

BACKUP_DIR.mkdir(parents=True, exist_ok=True)
SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)


def validate_python_ast(filepath: Path, code: str):
    if filepath.suffix.lower() == ".py":
        try:
            ast.parse(code, filename=str(filepath))
        except SyntaxError as err:
            raise SyntaxError(
                f"AST Синтаксическая ошибка в {filepath.name} [строка {err.lineno}, отступ {err.offset}]: {err.msg}"
            )


class AgentApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Local Zero-Click Agent (Port: 5050)")
        self.geometry("780x700")
        self.configure(bg=BG_MAIN)

        self.last_payload_hash = None
        self.last_payload_time = 0.0
        self.is_busy = False

        try:
            with open(LOG_FILE, "w", encoding="utf-8") as f:
                f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] === Лог агента инициализирован (main.log очищен) ===\n")
        except Exception:
            pass

        self._build_ui()
        self._bind_hotkeys_and_menu()
        self._start_http_server()

    def _build_ui(self):
        header_frame = tk.Frame(self, bg=BG_MAIN)
        header_frame.pack(fill="x", padx=15, pady=(10, 2))

        self.label_input = tk.Label(
            header_frame,
            text="JSON payload (ручной ввод или Zero-Click расширение):",
            bg=BG_MAIN,
            fg=TEXT_COLOR,
            font=("Segoe UI", 10, "bold"),
        )
        self.label_input.pack(side="left")

        self.btn_paste = tk.Button(
            header_frame,
            text="Вставить из буфера",
            bg=BTN_SECONDARY,
            fg=TEXT_COLOR,
            relief="flat",
            font=("Segoe UI", 9),
            cursor="hand2",
            command=self.paste_from_clipboard,
        )
        self.btn_paste.pack(side="right")

        self.text_input = scrolledtext.ScrolledText(
            self,
            height=11,
            bg=BG_INPUT,
            fg=TEXT_COLOR,
            insertbackground=TEXT_COLOR,
            font=("Consolas", 10),
            relief="flat",
            padx=8,
            pady=8,
            undo=True,
        )
        self.text_input.pack(fill="x", padx=15, pady=5)

        self.btn_submit = tk.Button(
            self,
            text="Выполнить команду",
            bg=BTN_COLOR,
            fg=TEXT_COLOR,
            activebackground="#483D8B",
            activeforeground=TEXT_COLOR,
            font=("Segoe UI", 11, "bold"),
            relief="flat",
            cursor="hand2",
            command=lambda: self.execute_task_threaded(self.text_input.get("1.0", tk.END)),
        )
        self.btn_submit.pack(fill="x", padx=15, pady=8)

        self.label_log = tk.Label(
            self,
            text="Лог агента (с AST валидацией синтаксиса):",
            bg=BG_MAIN,
            fg=TEXT_COLOR,
            font=("Segoe UI", 10, "bold"),
        )
        self.label_log.pack(anchor="w", padx=15, pady=(5, 2))

        self.text_log = scrolledtext.ScrolledText(
            self,
            height=14,
            bg="#202020",
            fg="#A9B7C6",
            font=("Consolas", 9),
            relief="flat",
            state="disabled",
            padx=8,
            pady=8,
        )
        self.text_log.pack(fill="both", expand=True, padx=15, pady=(0, 15))

    def _bind_hotkeys_and_menu(self):
        self.text_input.bind("<Key>", self._handle_ctrl_keys)
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="Вставить", command=self.paste_from_clipboard)
        self.context_menu.add_command(label="Копировать", command=self._copy_selection)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Очистить", command=lambda: self.text_input.delete("1.0", tk.END))
        self.text_input.bind("<Button-3>", lambda e: self.context_menu.tk_popup(e.x_root, e.y_root))

    def _handle_ctrl_keys(self, event):
        if event.state & 4:
            if event.keycode == 86:
                self.paste_from_clipboard()
                return "break"
            elif event.keycode == 65:
                self.text_input.tag_add("sel", "1.0", "end")
                return "break"
            elif event.keycode == 67:
                self._copy_selection()
                return "break"

    def paste_from_clipboard(self):
        try:
            text = self.clipboard_get()
            self.text_input.insert(tk.INSERT, text)
        except tk.TclError:
            pass

    def _copy_selection(self):
        try:
            sel = self.text_input.get("sel.first", "sel.last")
            self.clipboard_clear()
            self.clipboard_append(sel)
        except tk.TclError:
            pass

    def copy_to_clipboard_safe(self, text: str):
        self.after(0, self._set_clipboard, text)

    def _set_clipboard(self, text: str):
        self.clipboard_clear()
        self.clipboard_append(text)
        self.update()

    def log(self, message: str):
        ts = time.strftime("[%Y-%m-%d %H:%M:%S]")
        log_line = f"{ts} {message}\n"
        try:
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(log_line)
        except Exception:
            pass
        self.after(0, self._append_log, message)

    def _append_log(self, message: str):
        self.text_log.configure(state="normal")
        self.text_log.insert(tk.END, message + "\n")
        self.text_log.see(tk.END)
        self.text_log.configure(state="disabled")

    def _start_http_server(self):
        def run_server():
            server_address = ("127.0.0.1", SERVER_PORT)
            httpd = HTTPServer(server_address, self._create_handler())
            httpd.serve_forever()

        t = threading.Thread(target=run_server, daemon=True)
        t.start()
        self.log(f"[*] Zero-Click API мост слушает 127.0.0.1:{SERVER_PORT}")

    def _create_handler(self):
        app = self

        class AgentHandler(BaseHTTPRequestHandler):
            def _send_cors(self):
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
                self.send_header("Access-Control-Allow-Headers", "Content-Type")

            def do_OPTIONS(self):
                self.send_response(200)
                self._send_cors()
                self.end_headers()

            def do_POST(self):
                if self.path == "/log":
                    length = int(self.headers.get("Content-Length", 0))
                    body = self.rfile.read(length).decode("utf-8", errors="replace")
                    try:
                        log_data = json.loads(body)
                        msg = log_data.get("message", body)
                        lvl = log_data.get("level", "INFO")
                        app.log(f"[EXT-BG-{lvl}] {msg}")
                    except Exception:
                        app.log(f"[EXT-BG] {body}")
                    self.send_response(200)
                    self._send_cors()
                    self.send_header("Content-Type", "application/json; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(b'{"status":"ok"}')
                    return

                if self.path not in ("/run", "/execute"):
                    self.send_response(404)
                    self.end_headers()
                    return

                length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(length).decode("utf-8", errors="replace")
                app.log(f"[HTTP] Входящий POST {self.path} (размер: {length} байт)")
                try:
                    req_data = json.loads(body)
                    raw_text = req_data.get("raw_text", body)
                except Exception:
                    raw_text = body

                success, prompt = app.process_payload_sync(raw_text)

                self.send_response(200)
                self._send_cors()
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                resp_payload = {
                    "success": success,
                    "prompt": prompt,
                    "needs_reply": bool(prompt)
                }
                self.wfile.write(json.dumps(resp_payload, ensure_ascii=False).encode("utf-8"))

            def log_message(self, format, *args):
                pass

        return AgentHandler

    def execute_task_threaded(self, raw_text: str):
        self.log("[GUI] Ручной запуск задачи по кнопке в интерфейсе")
        self.btn_submit.config(state="disabled", text="Выполняется...")
        threading.Thread(target=lambda: self.process_payload_sync(raw_text), daemon=True).start()

    def process_payload_sync(self, raw_text: str) -> tuple[bool, str | None]:
        clean_text = re.sub(r"^```(?:json)?\s*", "", raw_text.strip(), flags=re.MULTILINE)
        clean_text = re.sub(r"\s*```$", "", clean_text, flags=re.MULTILINE).strip()

        if not clean_text:
            self.log("[ОШИБКА] Пустой запрос.")
            self.after(0, lambda: self.btn_submit.config(state="normal", text="Выполнить команду"))
            return False, "Ошибка: запрос был пуст."

        try:
            payload = json.loads(clean_text)
        except json.JSONDecodeError as e:
            err_msg = f"Невалидный JSON: {e}"
            self.log(f"[ОШИБКА JSON] {err_msg}")
            self.after(0, lambda: self.btn_submit.config(state="normal", text="Выполнить команду"))
            return False, f"Синтаксическая ошибка в сгенерированном JSON:\n{err_msg}"

        canonical_json = json.dumps(payload, sort_keys=True, ensure_ascii=False)
        payload_hash = hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()
        now = time.time()
        if payload_hash == self.last_payload_hash and (now - self.last_payload_time) < 30.0:
            self.log(f"[DEDUPLICATE] Игнорирование дубля запроса (хеш: {payload_hash[:8]}, интервал: {now - self.last_payload_time:.1f}с)")
            self.after(0, lambda: self.btn_submit.config(state="normal", text="Выполнить команду"))
            return True, None

        if self.is_busy:
            self.log("[BUSY] Агент уже выполняет другую задачу. Запрос отклонен.")
            self.after(0, lambda: self.btn_submit.config(state="normal", text="Выполнить команду"))
            return False, "Агент занят выполнением предыдущей команды."

        self.is_busy = True
        self.last_payload_hash = payload_hash
        self.last_payload_time = now

        last_cmd = None
        current_file = None
        collected_reports = []

        try:
            summary = payload.get("summary", "Без описания")
            self.log(f"\n=== Задача: {summary} ===")
            actions = payload.get("actions", [])

            for idx, act in enumerate(actions, start=1):
                atype = act.get("type")
                self.log(f"[{idx}/{len(actions)}] Действие: {atype}")

                if atype == "patch":
                    current_file = act.get("path")
                    self._action_patch(act)
                elif atype == "create":
                    current_file = act.get("path")
                    self._action_create(act)
                elif atype == "delete":
                    self._action_delete(act)
                elif atype in ("command", "query"):
                    last_cmd = act.get("cmd")
                    cmd_out = self._action_command(act)
                    if atype == "query" or act.get("report"):
                        collected_reports.append(f"[Команда: {last_cmd}]\n{cmd_out.strip()}")

            self.log("\n>>> DONE: Все действия и тесты пройдены! <<<\n")
            self.after(0, lambda: self.text_input.delete("1.0", tk.END))
            self.after(0, lambda: self.btn_submit.config(state="normal", text="Выполнить команду"))

            if collected_reports:
                reports_text = "\n\n".join(collected_reports)
                report_prompt = (
                    f"[System Report: {summary}]\n"
                    f"{reports_text}\n\n"
                    f"Все действия выполнены успешно. Проанализируй отчет и ответь пользователю ТЕКСТОМ без JSON-блоков."
                )
                self.log(f"  -> [ОТЧЕТ] Собран отчет по {len(collected_reports)} командам для отправки в чат.")
                self.copy_to_clipboard_safe(report_prompt)
                self.is_busy = False
                return False, report_prompt

            self.is_busy = False
            return True, None

        except Exception as err:
            self.is_busy = False
            self.log(f"\n[ОШИБКА ИСПОЛНЕНИЯ]: {err}")
            reverse_prompt = self._build_feedback_prompt(err, last_cmd, current_file)
            self.copy_to_clipboard_safe(reverse_prompt)
            self.log("[FEEDBACK] Промпт отправлен мосту и скопирован в буфер.")
            self.after(0, lambda: self.btn_submit.config(state="normal", text="Выполнить команду"))
            return False, reverse_prompt

    def _build_feedback_prompt(self, error: Exception, cmd: str | None, filepath: str | None) -> str:
        prompt_lines = [
            "При выполнении инструкций возникла ошибка.",
            f"Описание ошибки:\n{str(error)}"
        ]
        if cmd:
            prompt_lines.append(f"\nУпавшая команда:\n{cmd}")

        if filepath and Path(filepath).exists():
            try:
                code_snapshot = Path(filepath).read_text(encoding="utf-8")
                prompt_lines.append(f"\nТекущее состояние файла '{filepath}':\n```python\n{code_snapshot}\n```")
            except Exception:
                pass

        prompt_lines.append("\nИсправь ошибку и сгенерируй новый валидный JSON без лишнего текста.")
        return "\n".join(prompt_lines)

    def _action_patch(self, act: dict):
        path = Path(act["path"])
        if not path.is_absolute():
            path = BASE_DIR / path
        if not path.exists():
            raise FileNotFoundError(f"Файл не найден: {path}")

        search = act["search"].replace("\r\n", "\n")
        replace = act["replace"].replace("\r\n", "\n")
        content = path.read_text(encoding="utf-8").replace("\r\n", "\n")

        if search not in content:
            raise ValueError(f"Фрагмент не найден в {path}:\n{search}")

        new_content = content.replace(search, replace, 1)
        validate_python_ast(path, new_content)

        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        backup_file = BACKUP_DIR / f"{path.name}.bak"
        shutil.copyfile(path, backup_file)

        path.write_text(new_content, encoding="utf-8")
        self.log(f"  -> AST OK. Патч применен: {path} (бэкап в {backup_file})")

    def _action_create(self, act: dict):
        path = Path(act["path"])
        if not path.is_absolute():
            path = BASE_DIR / path
        content = act["content"]
        validate_python_ast(path, content)

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        self.log(f"  -> AST OK. Создан файл: {path}")

    def _action_delete(self, act: dict):
        path = Path(act["path"])
        if not path.is_absolute():
            path = BASE_DIR / path
        if path.exists():
            path.unlink()
            self.log(f"  -> Удален файл: {path}")

    def _try_autoinstall_missing_module(self, error_text: str, env: dict) -> bool:
        pkg_map = {
            "cv2": "opencv-python",
            "yaml": "pyyaml",
            "PIL": "pillow",
            "bs4": "beautifulsoup4",
            "sklearn": "scikit-learn",
            "serial": "pyserial",
            "OpenGL": "PyOpenGL"
        }
        match = re.search(r"(?:ModuleNotFoundError|ImportError):\s+No module named ['\"]([^'\"]+)['\"]", error_text)
        if not match:
            return False

        root_mod = match.group(1).split(".")[0]
        pkg_name = pkg_map.get(root_mod, root_mod)

        self.log(f"  [AUTO-PIP] Не найден модуль '{root_mod}'. Запуск автоустановки пакета '{pkg_name}'...")
        pip_cmd = f'"{sys.executable}" -m pip install {pkg_name}'
        pip_res = subprocess.run(pip_cmd, shell=True, capture_output=True, env=env)
        out = pip_res.stdout.decode("cp866", errors="replace") if pip_res.stdout else ""
        err = pip_res.stderr.decode("cp866", errors="replace") if pip_res.stderr else ""

        if pip_res.returncode == 0:
            self.log(f"  [AUTO-PIP] Пакет '{pkg_name}' успешно установлен!")
            return True
        else:
            self.log(f"  [AUTO-PIP] Ошибка установки '{pkg_name}':\n{err or out}")
            return False

    def _action_command(self, act: dict) -> str:
        cmd = act["cmd"]
        cwd = act.get("cwd")
        target_cwd = str(Path(cwd).resolve()) if cwd else str(BASE_DIR)
        self.log(f"  -> Запуск: {cmd}" + (f" [в {target_cwd}]" if cwd else ""))

        env = os.environ.copy()
        py_dir = Path(sys.executable).parent
        try:
            user_scripts = Path(site.getuserbase()) / "Scripts"
        except Exception:
            user_scripts = Path(os.path.expandvars(r"%APPDATA%\Python\Python310\Scripts"))

        for root_dir in [
            os.environ.get("ProgramFiles", "C:/Program Files"),
            os.environ.get("ProgramFiles(x86)", "C:/Program Files (x86)"),
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs")
        ]:
            if root_dir and os.path.exists(root_dir):
                try:
                    for item in os.listdir(root_dir):
                        if "PyCharm" in item:
                            bin_p = os.path.join(root_dir, item, "bin")
                            if os.path.exists(bin_p):
                                env["PATH"] = f"{bin_p};{env.get('PATH', '')}"
                except Exception:
                    pass

        scripts_path = str(SCRIPTS_DIR.resolve())
        env["PYTHONPATH"] = f"{scripts_path};{str(BASE_DIR)};{env.get('PYTHONPATH', '')}"
        env["PATH"] = f"{scripts_path};{user_scripts};{py_dir / 'Scripts'};{py_dir};{env.get('PATH', '')}"

        max_attempts = 3
        last_output = ""
        for attempt in range(1, max_attempts + 1):
            res = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                env=env,
                cwd=target_cwd,
            )

            stdout_text = res.stdout.decode("cp866", errors="replace") if res.stdout else ""
            stderr_text = res.stderr.decode("cp866", errors="replace") if res.stderr else ""
            last_output = stdout_text if stdout_text else stderr_text

            if res.returncode != 0:
                combined = f"{stderr_text}\n{stdout_text}"
                if attempt < max_attempts and self._try_autoinstall_missing_module(combined, env):
                    self.log(f"  [AUTO-PIP] Повторный запуск команды (попытка {attempt + 1})...")
                    continue

            if stdout_text:
                self.log(f"[STDOUT]:\n{stdout_text.strip()}")
            if stderr_text:
                self.log(f"[STDERR]:\n{stderr_text.strip()}")

            if res.returncode != 0:
                error_details = stderr_text if stderr_text else stdout_text
                raise RuntimeError(f"Команда '{cmd}' завершилась с кодом {res.returncode}.\nВывод:\n{error_details}")
            break

        return last_output


if __name__ == "__main__":
    app = AgentApp()
    app.mainloop()
