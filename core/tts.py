"""TTS发音模块，基于pyttsx3实现离线发音"""
import pyttsx3
import threading
import logging
import pythoncom

logger = logging.getLogger(__name__)


class TTSEngine:
    """文本转语音引擎，支持离线中英文发音"""

    def __init__(self):
        self._lock = threading.Lock()
        self._rate = 150
        self._voices_cache = None
        self._cache_voices()

    def _cache_voices(self):
        """在主线程中缓存语音列表，避免子线程中访问COM对象"""
        try:
            engine = pyttsx3.init()
            self._voices_cache = []
            for v in engine.getProperty("voices"):
                self._voices_cache.append({
                    "id": v.id,
                    "name": v.name,
                    "languages": list(v.languages) if v.languages else [],
                })
            engine.stop()
        except Exception as e:
            logger.error(f"缓存语音列表失败: {e}")
            self._voices_cache = []

    def speak(self, text, lang="en"):
        """异步朗读文本"""
        if not text:
            return

        thread = threading.Thread(target=self._speak_sync, args=(text, lang), daemon=True)
        thread.start()

    def _speak_sync(self, text, lang):
        """同步朗读文本（在子线程中执行，创建独立的引擎实例）"""
        with self._lock:
            engine = None
            try:
                pythoncom.CoInitialize()
                engine = pyttsx3.init()
                engine.setProperty("rate", self._rate)

                voice_id = self._select_voice(lang)
                if voice_id:
                    engine.setProperty("voice", voice_id)

                engine.say(text)
                engine.runAndWait()
            except Exception as e:
                logger.error(f"朗读失败: {e}")
            finally:
                if engine:
                    try:
                        engine.stop()
                    except Exception:
                        pass
                try:
                    pythoncom.CoUninitialize()
                except Exception:
                    pass

    def _select_voice(self, lang):
        """根据语言选择合适的语音ID"""
        if not self._voices_cache:
            return None

        if lang == "zh":
            for voice in self._voices_cache:
                name_lower = voice["name"].lower()
                if "chinese" in name_lower or "zh" in name_lower or "huihui" in name_lower or "yaoyao" in name_lower:
                    return voice["id"]
        else:
            for voice in self._voices_cache:
                name_lower = voice["name"].lower()
                if "english" in name_lower or "zira" in name_lower or "david" in name_lower:
                    return voice["id"]

        return self._voices_cache[0]["id"] if self._voices_cache else None

    def set_rate(self, rate):
        """设置语速"""
        self._rate = rate

    def get_rate(self):
        """获取当前语速"""
        return self._rate

    def stop(self):
        """停止朗读"""
        pass

    def get_voices(self):
        """获取可用的语音列表"""
        return self._voices_cache or []
