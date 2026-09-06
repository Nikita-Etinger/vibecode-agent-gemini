import pyautogui
from tools import hid_controller

def test_hid_exports():
    assert hasattr(hid_controller, 'click')
    assert hasattr(hid_controller, 'drag')
    assert hasattr(hid_controller, 'write')
    assert hasattr(hid_controller, 'hotkey')
