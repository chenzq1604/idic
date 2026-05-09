"""历史记录数据模型"""
import sqlite3
import os
from datetime import datetime
from utils.paths import get_writable_path


class HistoryManager:
    """查询历史记录管理器，使用SQLite存储"""

    DB_PATH = get_writable_path("idic.db")

    def __init__(self):
        self._init_db()

    def _init_db(self):
        """初始化数据库表"""
        os.makedirs(os.path.dirname(self.DB_PATH), exist_ok=True)
        conn = sqlite3.connect(self.DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                word TEXT NOT NULL,
                query_time TEXT NOT NULL
            )
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_history_word
            ON history(word)
        """)
        conn.commit()
        conn.close()

    def add(self, word):
        """添加查询记录"""
        conn = sqlite3.connect(self.DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO history (word, query_time) VALUES (?, ?)",
            (word, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        conn.commit()
        conn.close()

    def get_recent(self, limit=50):
        """获取最近的查询记录"""
        conn = sqlite3.connect(self.DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT word, query_time FROM history ORDER BY id DESC LIMIT ?",
            (limit,)
        )
        rows = cursor.fetchall()
        conn.close()
        return [{"word": row[0], "time": row[1]} for row in rows]

    def search(self, keyword, limit=20):
        """搜索历史记录"""
        conn = sqlite3.connect(self.DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT DISTINCT word FROM history WHERE word LIKE ? ORDER BY id DESC LIMIT ?",
            (f"%{keyword}%", limit)
        )
        rows = cursor.fetchall()
        conn.close()
        return [row[0] for row in rows]

    def clear(self):
        """清空历史记录"""
        conn = sqlite3.connect(self.DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM history")
        conn.commit()
        conn.close()
