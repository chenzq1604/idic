"""PyInstaller 打包脚本 - 将 Python 后端打包为 exe"""
import os
import sys
import shutil
import subprocess
import glob

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
DIST_DIR = os.path.join(BASE_DIR, "backend-dist")
BUILD_DIR = os.path.join(BASE_DIR, "build_temp")


def check_pyinstaller():
    """检查 PyInstaller 是否已安装"""
    try:
        import PyInstaller
        print(f"PyInstaller 版本: {PyInstaller.__version__}")
    except ImportError:
        print("PyInstaller 未安装，正在安装...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])


def clean_build():
    """清理旧的构建产物"""
    for d in [DIST_DIR, BUILD_DIR]:
        if os.path.exists(d):
            shutil.rmtree(d)
            print(f"已清理: {d}")


def find_conda_dlls():
    """查找 conda 环境中缺失的 DLL 文件"""
    conda_prefix = os.path.dirname(sys.executable)
    library_bin = os.path.join(conda_prefix, "Library", "bin")

    dll_patterns = [
        "liblzma.dll", "libbz2.dll", "libssl*.dll",
        "libcrypto*.dll", "ffi*.dll", "libexpat.dll", "sqlite3.dll"
    ]

    found_dlls = []
    if not os.path.exists(library_bin):
        print(f"警告: conda Library/bin 目录不存在: {library_bin}")
        return found_dlls

    for pattern in dll_patterns:
        matches = glob.glob(os.path.join(library_bin, pattern))
        if matches:
            for m in matches:
                found_dlls.append(m)
                print(f"找到 DLL: {m}")
        else:
            print(f"警告: 未找到 DLL 匹配: {pattern}")

    return found_dlls


def build_backend():
    """使用 PyInstaller 打包后端"""
    main_py = os.path.join(BACKEND_DIR, "main.py")

    if not os.path.exists(main_py):
        print(f"错误: 找不到 {main_py}")
        sys.exit(1)

    db_zip_ecdict = os.path.join(BASE_DIR, "resources", "db", "ecdict.db.zip")
    db_zip_cedict = os.path.join(BASE_DIR, "resources", "db", "cedict.db.zip")
    llm_configs = os.path.join(BASE_DIR, "resources", "llm_configs.json")
    settings_json = os.path.join(BASE_DIR, "resources", "settings.json")

    datas_args = []

    for f in [db_zip_ecdict, db_zip_cedict, llm_configs, settings_json]:
        if os.path.exists(f):
            datas_args.extend(["--add-data", f"{f};resources"])
            print(f"添加数据文件: {f}")
        else:
            print(f"警告: 数据文件不存在: {f}")

    dll_files = find_conda_dlls()
    for dll in dll_files:
        datas_args.extend(["--add-binary", f"{dll};."])

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", "idic-backend",
        "--onedir",
        "--noconfirm",
        "--clean",
        "--workpath", BUILD_DIR,
        "--distpath", DIST_DIR,
        "--paths", BASE_DIR,
        "--hidden-import", "uvicorn.logging",
        "--hidden-import", "uvicorn.loops",
        "--hidden-import", "uvicorn.loops.auto",
        "--hidden-import", "uvicorn.protocols",
        "--hidden-import", "uvicorn.protocols.http",
        "--hidden-import", "uvicorn.protocols.http.auto",
        "--hidden-import", "uvicorn.protocols.websockets",
        "--hidden-import", "uvicorn.protocols.websockets.auto",
        "--hidden-import", "uvicorn.lifespan",
        "--hidden-import", "uvicorn.lifespan.on",
        "--hidden-import", "core.dictionary",
        "--hidden-import", "core.chinese_dictionary",
        "--hidden-import", "core.translator",
        "--hidden-import", "utils.paths",
        "--hidden-import", "utils.db",
        "--hidden-import", "models.llm_config",
        "--hidden-import", "models.history",
    ]

    cmd.extend(datas_args)
    cmd.append(main_py)

    print("\n" + "=" * 60)
    print("开始打包 Python 后端...")
    print("=" * 60 + "\n")

    subprocess.check_call(cmd)

    print("\n" + "=" * 60)
    print("Python 后端打包完成!")
    print(f"输出目录: {DIST_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    check_pyinstaller()
    clean_build()
    build_backend()
