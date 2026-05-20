"""数据库工具模块"""
import sqlite3
import os
from utils.paths import get_resource_path, get_writable_path


def get_db_path(db_name="idic.db"):
    """获取数据库文件路径"""
    if db_name in ("idic.db",):
        return get_writable_path(db_name)
    return get_resource_path(os.path.join("db", db_name))


def get_connection(db_name="idic.db"):
    """获取数据库连接"""
    db_path = get_db_path(db_name)
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def execute_query(sql, params=None, db_name="idic.db"):
    """执行查询SQL并返回结果（强制参数化查询）"""
    conn = get_connection(db_name)
    try:
        cursor = conn.cursor()
        cursor.execute(sql, params or ())
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def execute_update(sql, params=None, db_name="idic.db"):
    """执行更新SQL（强制参数化查询）"""
    conn = get_connection(db_name)
    try:
        cursor = conn.cursor()
        cursor.execute(sql, params or ())
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()
