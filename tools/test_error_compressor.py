from tools.error_compressor import clean_ansi_codes, compress_error_log, compress_code_snapshot


def test_clean_ansi_codes():
    colored = "\x1b[31mRed text\x1b[0m normal"
    assert clean_ansi_codes(colored) == "Red text normal"


def test_compress_error_log_short():
    err = "ZeroDivisionError: division by zero"
    assert compress_error_log(err, max_chars=200) == err


def test_compress_error_log_traceback_filters_site_packages():
    raw_trace = (
        "Traceback (most recent call last):\n"
        '  File "C:\\lib\\python3.10\\site-packages\\pkg\\core.py", line 40, in run\n'
        "    internal_call()\n"
        '  File "workspace\\app.py", line 15, in do_work\n'
        "    raise ValueError('bad input')\n"
        "ValueError: bad input"
    )
    compressed = compress_error_log(raw_trace, max_chars=300)
    assert "site-packages" not in compressed
    assert "workspace\\app.py" in compressed
    assert "ValueError: bad input" in compressed


def test_compress_error_log_huge_text():
    huge_text = "Start of error\n" + ("x" * 10000) + "\nEnd of error: FinalException"
    compressed = compress_error_log(huge_text, max_chars=500)
    assert len(compressed) <= 600
    assert "Start of error" in compressed
    assert "FinalException" in compressed
    assert "Вырезано" in compressed


def test_compress_code_snapshot():
    code = "print('start')\n" + ("# comment\n" * 500) + "print('end')"
    snapshot = compress_code_snapshot(code, max_chars=400)
    assert len(snapshot) <= 550
    assert "print('start')" in snapshot
    assert "print('end')" in snapshot
    assert "[остальной код скрыт" in snapshot
