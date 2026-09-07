import re


def clean_ansi_codes(text: str) -> str:
    ansi_regex = r"\x1B(?:\[[0-?]*[ -/]*[@-~]|[@-Z\\-_])"
    return re.sub(ansi_regex, "", text)


def compress_error_log(raw_error: str, max_chars: int = 1200) -> str:
    text = clean_ansi_codes(raw_error).strip()
    if not text:
        return "Неизвестная ошибка (вывод пуст)."

    lines = text.splitlines()
    if "Traceback (most recent call last):" in text:
        filtered_lines = []
        skip_body = False

        for line in lines:
            is_lib_frame = bool(re.search(r'File ".*[\\/](?:site-packages|lib[\\/]python\d(?:\.\d+)?)[\\/]', line, re.IGNORECASE))
            if is_lib_frame:
                skip_body = True
                continue
            if skip_body:
                if line.startswith("    ") and not line.strip().startswith("File "):
                    continue
                skip_body = False

            filtered_lines.append(line)

        text = "\n".join(filtered_lines)

    if len(text) <= max_chars:
        return text

    head_size = int(max_chars * 0.35)
    tail_size = int(max_chars * 0.55)

    head = text[:head_size].rstrip()
    tail = text[-tail_size:].lstrip()
    cut_chars = len(text) - len(head) - len(tail)

    return f"{head}\n\n... [Вырезано {cut_chars} симв. промежуточного лога] ...\n\n{tail}"


def compress_code_snapshot(code: str, max_chars: int = 2000) -> str:
    if len(code) <= max_chars:
        return code
    head = code[: int(max_chars * 0.45)].rstrip()
    tail = code[-int(max_chars * 0.45) :].lstrip()
    return f"{head}\n\n# ... [остальной код скрыт во избежание превышения лимитов чата] ...\n\n{tail}"
