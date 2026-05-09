"""中文词典查询引擎，基于CC-CEDICT数据库"""
import sqlite3
import os
import logging
from utils.paths import get_db_path

logger = logging.getLogger(__name__)


class ChineseDictionaryEngine:
    """中文词典查询引擎，支持从CC-CEDICT数据库查询中文词语"""

    DEFAULT_DB_PATH = get_db_path("cedict.db")

    def __init__(self, db_path=None):
        self.db_path = db_path or self.DEFAULT_DB_PATH
        self._conn = None

    def _get_connection(self):
        """获取数据库连接"""
        if self._conn is None:
            if not os.path.exists(self.db_path):
                logger.warning(f"中文词典数据库不存在: {self.db_path}")
                return None
            self._conn = sqlite3.connect(self.db_path)
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def lookup(self, word):
        """查询中文词语，返回词典信息

        Args:
            word: 中文词语（简体或繁体）

        Returns:
            查询结果列表，每项包含 traditional, simplified, pinyin, definitions
            未找到返回空列表，数据库不可用返回None
        """
        conn = self._get_connection()
        if conn is None:
            return None

        word = word.strip()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM cedict WHERE simplified = ? OR traditional = ?",
            (word, word)
        )
        rows = cursor.fetchall()

        if not rows:
            return []

        results = []
        for row in rows:
            definitions = row["definitions"].split('|') if row["definitions"] else []
            results.append({
                'traditional': row["traditional"],
                'simplified': row["simplified"],
                'pinyin': row["pinyin"],
                'definitions': definitions,
            })

        return results

    def suggest(self, prefix, limit=10):
        """根据前缀获取中文词语建议"""
        conn = self._get_connection()
        if conn is None:
            return []

        cursor = conn.cursor()
        cursor.execute(
            "SELECT DISTINCT simplified FROM cedict WHERE simplified LIKE ? ORDER BY simplified LIMIT ?",
            (f"{prefix}%", limit)
        )
        rows = cursor.fetchall()
        return [row["simplified"] for row in rows]

    def is_available(self):
        """检查词典数据库是否可用"""
        return os.path.exists(self.db_path)

    def close(self):
        """关闭数据库连接"""
        if self._conn:
            self._conn.close()
            self._conn = None
