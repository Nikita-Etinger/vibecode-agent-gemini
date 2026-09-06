import mss
import easyocr
import torch
import os
import sys

def get_reader():
    if not hasattr(sys, "_easyocr_reader") or sys._easyocr_reader is None:
        use_cuda = torch.cuda.is_available()
        print(f"[OCR] Инициализация EasyOCR Reader (CUDA={use_cuda})...")
        sys._easyocr_reader = easyocr.Reader(['ru', 'en'], gpu=use_cuda)
    return sys._easyocr_reader

def get_text_coordinates():
    reader = get_reader()
    print("[SYS] Захват экрана и распознавание (EasyOCR)...")
    img_path = "screenshot_tool.png"
    with mss.mss() as sct:
        sct.shot(mon=-1, output=img_path)
        
    results = reader.readtext(img_path)
    
    if os.path.exists(img_path):
        os.remove(img_path)
        
    elements = []
    for bbox, text, prob in results:
        if prob > 0.35 and text.strip():
            x = int((bbox[0][0] + bbox[2][0]) / 2)
            y = int((bbox[0][1] + bbox[2][1]) / 2)
            elements.append({"text": text, "x": x, "y": y})
            
    return elements
