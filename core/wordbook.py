"""生词本管理模块"""
import sqlite3
import os
from datetime import datetime
import logging
from utils.paths import get_writable_path

logger = logging.getLogger(__name__)


class WordbookManager:
    """生词本管理器，支持添加、删除、查询收藏的单词"""

    DB_PATH = get_writable_path("idic.db")

    def __init__(self):
        self._init_db()

    def _init_db(self):
        """初始化生词本数据表"""
        os.makedirs(os.path.dirname(self.DB_PATH), exist_ok=True)
        conn = sqlite3.connect(self.DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS wordbook (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                word TEXT NOT NULL UNIQUE,
                phonetic TEXT DEFAULT '',
                translation TEXT DEFAULT '',
                added_time TEXT NOT NULL
            )
        """)
        conn.commit()
        conn.close()

    def add_word(self, word, phonetic="", translation=""):
        """添加单词到生词本"""
        word = word.strip().lower()
        if not word:
            return False

        conn = sqlite3.connect(self.DB_PATH)
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT OR REPLACE INTO wordbook (word, phonetic, translation, added_time) VALUES (?, ?, ?, ?)",
                (word, phonetic, translation, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

    def remove_word(self, word):
        """从生词本删除单词"""
        conn = sqlite3.connect(self.DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM wordbook WHERE word = ?", (word.strip().lower(),))
        conn.commit()
        conn.close()

    def is_in_wordbook(self, word):
        """检查单词是否在生词本中"""
        conn = sqlite3.connect(self.DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM wordbook WHERE word = ?", (word.strip().lower(),))
        result = cursor.fetchone()
        conn.close()
        return result is not None

    def get_all_words(self):
        """获取生词本中所有单词"""
        conn = sqlite3.connect(self.DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM wordbook ORDER BY added_time DESC")
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def search_words(self, keyword):
        """搜索生词本中的单词"""
        conn = sqlite3.connect(self.DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM wordbook WHERE word LIKE ? ORDER BY added_time DESC",
            (f"%{keyword}%",)
        )
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def get_count(self):
        """获取生词本中的单词数量"""
        conn = sqlite3.connect(self.DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM wordbook")
        count = cursor.fetchone()[0]
        conn.close()
        return count
