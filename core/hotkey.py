"""全局热键模块"""
import threading
import logging

logger = logging.getLogger(__name__)


class HotkeyManager:
    """全局热键管理器，注册和管理全局快捷键"""

    def __init__(self):
        self._hotkeys = {}
        self._running = False

    def register(self, hotkey, callback):
        """注册全局热键"""
        try:
            import keyboard
            keyboard.add_hotkey(hotkey, callback, suppress=False)
            self._hotkeys[hotkey] = callback
            logger.info(f"已注册热键: {hotkey}")
            return True
        except Exception as e:
            logger.error(f"注册热键失败 {hotkey}: {e}")
            return False

    def unregister(self, hotkey):
        """取消注册热键"""
        try:
            import keyboard
            keyboard.remove_hotkey(hotkey)
            if hotkey in self._hotkeys:
                del self._hotkeys[hotkey]
            logger.info(f"已取消热键: {hotkey}")
        except Exception as e:
            logger.error(f"取消热键失败 {hotkey}: {e}")

    def unregister_all(self):
        """取消所有热键"""
        try:
            import keyboard
            keyboard.unhook_all()
            self._hotkeys.clear()
        except Exception as e:
            logger.error(f"取消所有热键失败: {e}")

    def get_registered_hotkeys(self):
        """获取已注册的热键列表"""
        return list(self._hotkeys.keys())
