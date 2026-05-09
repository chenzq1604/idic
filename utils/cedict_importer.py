"""CC-CEDICT 词典解析和导入工具

将 CC-CEDICT 原始文本文件解析并导入 SQLite 数据库，供查询引擎使用。

CC-CEDICT 格式说明:
  注释行以 # 开头
  数据行格式: 繁体 简体 [pin1 yin1] /释义1/释义2/.../
  示例: 年糕 年糕 [nian2 gao1] /New Year cake/sticky rice cake/

使用方法:
  python cedict_importer.py <cedict_file_path>

导入后会生成 cedict.db 文件在 resources/db/ 目录下。
"""
import sqlite3
import os
import re
import sys
import gzip
import zipfile
from utils.paths import get_db_path


DB_PATH = get_db_path("cedict.db")

CEDICT_LINE_PATTERN = re.compile(
    r'^(\S+)\s+(\S+)\s+\[([^\]]+)\]\s+/(.+)/$'
)


def parse_cedict_line(line):
    """解析单行CC-CEDICT数据

    Args:
        line: CC-CEDICT原始行

    Returns:
        解析后的字典，格式无效时返回None
    """
    line = line.strip()
    if not line or line.startswith('#'):
        return None

    match = CEDICT_LINE_PATTERN.match(line)
    if not match:
        return None

    traditional = match.group(1)
    simplified = match.group(2)
    pinyin = match.group(3)
    definitions = match.group(4).split('/')

    definitions = [d.strip() for d in definitions if d.strip()]

    return {
        'traditional': traditional,
        'simplified': simplified,
        'pinyin': pinyin,
        'definitions': definitions,
    }


def import_cedict(cedict_path, db_path=None):
    """导入CC-CEDICT文件到SQLite数据库

    Args:
        cedict_path: CC-CEDICT原始文件路径（.txt, .gz 或 .zip）
        db_path: 输出数据库路径，默认为 resources/db/cedict.db
    """
    if db_path is None:
        db_path = DB_PATH

    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    if os.path.exists(db_path):
        os.remove(db_path)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE cedict (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            traditional TEXT NOT NULL,
            simplified TEXT NOT NULL,
            pinyin TEXT NOT NULL,
            definitions TEXT NOT NULL
        )
    """)

    cursor.execute("CREATE INDEX idx_simplified ON cedict(simplified)")
    cursor.execute("CREATE INDEX idx_traditional ON cedict(traditional)")
    cursor.execute("CREATE INDEX idx_pinyin ON cedict(pinyin)")

    lines = _read_cedict_file(cedict_path)

    count = 0
    batch = []
    batch_size = 5000

    for line in lines:
        entry = parse_cedict_line(line)
        if entry is None:
            continue

        definitions_str = '|'.join(entry['definitions'])
        batch.append((
            entry['traditional'],
            entry['simplified'],
            entry['pinyin'],
            definitions_str,
        ))

        if len(batch) >= batch_size:
            cursor.executemany(
                "INSERT INTO cedict (traditional, simplified, pinyin, definitions) VALUES (?, ?, ?, ?)",
                batch
            )
            count += len(batch)
            batch = []
            if count % 50000 == 0:
                print(f"  已导入 {count} 条...")

    if batch:
        cursor.executemany(
            "INSERT INTO cedict (traditional, simplified, pinyin, definitions) VALUES (?, ?, ?, ?)",
            batch
        )
        count += len(batch)

    conn.commit()
    conn.close()

    print(f"导入完成！共 {count} 条词条，数据库: {db_path}")
    return count


def _read_cedict_file(cedict_path):
    """读取CC-CEDICT文件，支持.txt/.gz/.zip格式"""
    if cedict_path.endswith('.gz'):
        with gzip.open(cedict_path, 'rt', encoding='utf-8') as f:
            return f.readlines()
    elif cedict_path.endswith('.zip'):
        with zipfile.ZipFile(cedict_path, 'r') as zf:
            names = zf.namelist()
            txt_files = [n for n in names if n.endswith('.txt') or n.endswith('.utf8') or n.endswith('.u8')]
            if not txt_files:
                raise ValueError(f"ZIP中未找到.txt文件: {names}")
            with zf.open(txt_files[0]) as f:
                return f.read().decode('utf-8').splitlines(keepends=True)
    else:
        with open(cedict_path, 'r', encoding='utf-8') as f:
            return f.readlines()


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: python cedict_importer.py <cedict_file_path>")
        print("  cedict_file_path: CC-CEDICT文件路径 (.txt / .gz / .zip)")
        sys.exit(1)

    cedict_file = sys.argv[1]
    if not os.path.exists(cedict_file):
        print(f"文件不存在: {cedict_file}")
        sys.exit(1)

    import_cedict(cedict_file)
