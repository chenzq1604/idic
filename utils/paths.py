"""资源路径解析模块，兼容开发环境和PyInstaller打包环境"""
import os
import sys
import shutil
import zipfile
import logging

logger = logging.getLogger(__name__)


def get_base_dir():
    """获取项目根目录，兼容PyInstaller打包环境"""
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_resource_path(relative_path):
    """获取只读资源文件的绝对路径（如数据库等）

    Args:
        relative_path: 相对于resources目录的路径，如 'db/ecdict.db'

    Returns:
        资源文件的绝对路径
    """
    return os.path.join(get_base_dir(), "resources", relative_path)


def get_data_dir():
    """获取可写数据目录（用户数据目录）

    打包后数据文件存放在 %APPDATA%/iDic/ 目录下，
    首次运行时从打包目录复制初始文件

    Returns:
        用户数据目录的绝对路径
    """
    if getattr(sys, 'frozen', False):
        app_data = os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), 'iDic')
        os.makedirs(app_data, exist_ok=True)
        return app_data
    else:
        return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resources")


def get_writable_path(filename):
    """获取可写数据文件的绝对路径

    首次运行时从打包目录复制初始文件到用户数据目录

    Args:
        filename: 文件名，如 'idic.db'、'llm_configs.json'

    Returns:
        数据文件的绝对路径
    """
    data_dir = get_data_dir()
    dest = os.path.join(data_dir, filename)

    if getattr(sys, 'frozen', False) and not os.path.exists(dest):
        src = os.path.join(get_base_dir(), "resources", filename)
        if os.path.exists(src):
            shutil.copy2(src, dest)

    return dest


def get_db_path(db_name):
    """获取数据库文件路径，支持自动解压

    打包环境下，数据库zip文件随exe分发，首次运行时自动解压到用户数据目录。
    开发环境下直接使用resources/db/下的原始文件。

    Args:
        db_name: 数据库文件名，如 'ecdict.db'、'cedict.db'

    Returns:
        数据库文件的绝对路径
    """
    if getattr(sys, 'frozen', False):
        data_dir = get_data_dir()
        db_dir = os.path.join(data_dir, "db")
        os.makedirs(db_dir, exist_ok=True)
        db_path = os.path.join(db_dir, db_name)

        if not os.path.exists(db_path):
            zip_path = os.path.join(get_base_dir(), "resources", "db", db_name + ".zip")
            if os.path.exists(zip_path):
                logger.info(f"首次运行，正在解压 {db_name}，请稍候...")
                try:
                    with zipfile.ZipFile(zip_path, 'r') as zf:
                        zf.extractall(db_dir)
                    logger.info(f"{db_name} 解压完成")
                except Exception as e:
                    logger.error(f"解压 {db_name} 失败: {e}")
            else:
                src_db = os.path.join(get_base_dir(), "resources", "db", db_name)
                if os.path.exists(src_db):
                    shutil.copy2(src_db, db_path)

        return db_path
    else:
        return os.path.join(get_base_dir(), "resources", "db", db_name)
