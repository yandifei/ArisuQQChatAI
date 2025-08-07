"""热键管理（hotkey_manager）
管理快捷键和全局热键
"""

import win32con
from ctypes import *
from ctypes.wintypes import *
from PyQt6.QtCore import QThread
# 第三方库
from PyQt6.QtCore import QObject, pyqtSignal
import keyboard # 全局热键

class GlobalHotkeyManager(QObject):
    # 构建热键信号
    hotkey_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.hotkeys = {}

    def register_hotkey(self, name, key_combination):
        """注册全局热键"""
        try:
            # # 移除旧热键（如果存在）
            # if name in self.hotkeys:
            #     keyboard.remove_hotkey(self.hotkeys[name])

            # 添加新热键
            self.hotkeys[name] = keyboard.add_hotkey(
                key_combination,
                lambda: self.hotkey_signal.emit(name)
            )
            return True
        except Exception as e:
            print(f"注册热键失败: {e}")
            return False

    def unregister_hotkey(self, name):
        """取消注册热键"""
        if name in self.hotkeys:
            keyboard.remove_hotkey(self.hotkeys[name])
            del self.hotkeys[name]
            return True
        return False




# 这里的 QMThread 为自定义的 QThread
class HotKey(QThread):
    """全局热键监听"""
    ShowWindow = pyqtSignal(int)

    def __init__(self):
        super(HotKey, self).__init__()

        self.main_key = 192

    def run(self):
        """ 监听 windows 快捷键使用 """

        user32 = windll.user32

        while True:
            if not user32.RegisterHotKey(None, 1, win32con.MOD_ALT, self.main_key):  # alt+~
                print('Unable to register id', self.key_num, self.key_num % 2)

            try:
                msg = MSG()

                if user32.GetMessageA(byref(msg), None, 0, 0) != 0:
                    print('2222222', msg.message, win32con.WM_HOTKEY)
                    if msg.message == win32con.WM_HOTKEY:
                        if msg.wParam == win32con.MOD_ALT:
                            self.ShowWindow.emit(msg.lParam)

            finally:
                print('finish')



