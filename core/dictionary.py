"""离线词典查询引擎，基于ECDICT数据库"""
import sqlite3
import os
import logging
from utils.paths import get_db_path

logger = logging.getLogger(__name__)


class DictionaryEngine:
    """离线词典查询引擎，支持从ECDICT数据库查询单词释义"""

    DEFAULT_DB_PATH = get_db_path("ecdict.db")

    def __init__(self, db_path=None):
        self.db_path = db_path or self.DEFAULT_DB_PATH
        self._conn = None

    def _get_connection(self):
        """获取数据库连接"""
        if self._conn is None:
            if not os.path.exists(self.db_path):
                logger.warning(f"词典数据库不存在: {self.db_path}")
                return None
            self._conn = sqlite3.connect(self.db_path)
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def lookup(self, word):
        """查询单词，返回词典信息"""
        conn = self._get_connection()
        if conn is None:
            return None

        word = word.strip().lower()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM stardict WHERE word = ?", (word,))
        row = cursor.fetchone()

        if row is None:
            cursor.execute("SELECT * FROM stardict WHERE word = ?", (word.capitalize(),))
            row = cursor.fetchone()

        if row is None:
            return None

        return self._parse_row(row)

    def suggest(self, prefix, limit=10):
        """根据前缀获取单词建议"""
        conn = self._get_connection()
        if conn is None:
            return []

        cursor = conn.cursor()
        cursor.execute(
            "SELECT word FROM stardict WHERE word LIKE ? ORDER BY word LIMIT ?",
            (f"{prefix.lower()}%", limit)
        )
        rows = cursor.fetchall()
        return [row["word"] for row in rows]

    def _parse_row(self, row):
        """解析数据库行，返回结构化的词典数据"""
        result = {
            "word": row["word"],
            "phonetic": row["phonetic"] if "phonetic" in row.keys() else "",
            "definition": row["definition"] if "definition" in row.keys() else "",
            "translation": row["translation"] if "translation" in row.keys() else "",
            "pos": row["pos"] if "pos" in row.keys() else "",
            "collins": row["collins"] if "collins" in row.keys() else 0,
            "oxford": row["oxford"] if "oxford" in row.keys() else 0,
            "tag": row["tag"] if "tag" in row.keys() else "",
            "exchange": row["exchange"] if "exchange" in row.keys() else "",
        }

        result["definitions"] = self._parse_definitions(result["definition"])
        result["translations"] = self._parse_translations(result["translation"])

        return result

    def _parse_definitions(self, definition_str):
        """解析英文释义，按词性分组"""
        if not definition_str:
            return []
        definitions = []
        for item in definition_str.split("\\n"):
            item = item.strip()
            if item:
                definitions.append(item)
        return definitions

    def _parse_translations(self, translation_str):
        """解析中文翻译，按词性分组"""
        if not translation_str:
            return []
        translations = []
        for item in translation_str.split("\\n"):
            item = item.strip()
            if item:
                translations.append(item)
        return translations

    def is_available(self):
        """检查词典数据库是否可用"""
        return os.path.exists(self.db_path)

    def close(self):
        """关闭数据库连接"""
        if self._conn:
            self._conn.close()
            self._conn = None
