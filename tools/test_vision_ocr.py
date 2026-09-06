from tools import vision_ocr

def test_ocr_interface():
    assert hasattr(vision_ocr, 'get_reader')
    assert hasattr(vision_ocr, 'get_text_coordinates')
