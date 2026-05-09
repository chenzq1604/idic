"""剪贴板监听模块，使用Windows原生API读取剪贴板"""
import threading
import time
import ctypes
import logging

logger = logging.getLogger(__name__)


def _read_clipboard():
    """使用Windows原生API读取剪贴板文本"""
    try:
        CF_UNICODETEXT = 13
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32

        if not user32.OpenClipboard(0):
            return ""

        try:
            handle = user32.GetClipboardData(CF_UNICODETEXT)
            if not handle:
                return ""
            pointer = kernel32.GlobalLock(handle)
            if not pointer:
                return ""
            try:
                return ctypes.c_wchar_p(pointer).value or ""
            finally:
                kernel32.GlobalUnlock(handle)
        finally:
            user32.CloseClipboard()
    except Exception:
        return ""


class ClipboardListener:
    """剪贴板监听器，当剪贴板内容变化时触发回调"""

    def __init__(self, callback=None, interval=0.3):
        self.callback = callback
        self.interval = interval
        self._running = False
        self._thread = None
        self._last_content = ""

    def start(self):
        """启动监听"""
        if self._running:
            return
        self._running = True
        self._last_content = _read_clipboard()
        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()
        logger.info("剪贴板监听已启动")

    def stop(self):
        """停止监听"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
        logger.info("剪贴板监听已停止")

    def _listen_loop(self):
        """监听循环"""
        while self._running:
            try:
                current = _read_clipboard()
                if current and current != self._last_content and current.strip():
                    self._last_content = current
                    if self.callback:
                        self.callback(current.strip())
            except Exception as e:
                logger.error(f"剪贴板读取错误: {e}")
            time.sleep(self.interval)

    def set_callback(self, callback):
        """设置回调函数"""
        self.callback = callback

    @property
    def is_running(self):
        """监听器是否正在运行"""
        return self._running
