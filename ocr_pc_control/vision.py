import mss
import easyocr
import os
import time
import sys

def get_screen_data():
    img_path = "screenshot.png"
    with mss.mss() as sct:
        sct.shot(mon=-1, output=img_path)
    # Инициализация OCR
    reader = easyocr.Reader(['ru', 'en'])
    results = reader.readtext(img_path)
    if os.path.exists(img_path):
        os.remove(img_path)
    return results

def main():
    # Игнорируем нечитаемые символы при выводе в консоль Windows
    sys.stdout.reconfigure(errors='replace')

    print("[SYS] Захват экрана и распознавание (EasyOCR)...")
    start = time.time()
    results = get_screen_data()
    print("--- РЕЗУЛЬТАТЫ OCR ---")
    for bbox, text, prob in results:
        if prob > 0.35 and text.strip():
            x = int((bbox[0][0] + bbox[2][0]) / 2)
            y = int((bbox[0][1] + bbox[2][1]) / 2)
            print(f"[X:{x:4d}, Y:{y:4d}] {text}")
    print(f"[OK] Выполнено за {time.time() - start:.2f} сек.")

if __name__ == '__main__':
    main()
