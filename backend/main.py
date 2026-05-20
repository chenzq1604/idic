"""iDic 后端服务 - FastAPI"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import sys
import os
import json
import hashlib
import uuid
import re
from datetime import datetime


def get_base_dir():
    """获取项目根目录，兼容PyInstaller打包环境"""
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    this_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(this_dir)
    idic_dir = os.path.join(os.path.dirname(project_dir), 'idic')
    if os.path.isdir(os.path.join(idic_dir, 'core')):
        return idic_dir
    return project_dir


def get_data_dir():
    """获取可写数据目录（打包后使用 %APPDATA%/iDic/）"""
    if getattr(sys, 'frozen', False):
        app_data = os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), 'iDic')
        os.makedirs(app_data, exist_ok=True)
        return app_data
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


BASE_DIR = get_base_dir()
DATA_DIR = get_data_dir()

sys.path.insert(0, BASE_DIR)

from core.dictionary import DictionaryEngine
from core.chinese_dictionary import ChineseDictionaryEngine
from core.translator import LLMTranslator as Translator

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 桌面应用，后端仅监听127.0.0.1，安全风险可控
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ModelConfigItem(BaseModel):
    id: Optional[str] = None
    name: str = ""
    modelName: str = ""
    apiKey: str = ""
    apiBase: str = ""
    timeout: int = 60
    testResult: str = ""
    testSuccess: bool = False
    testTime: str = ""


class ProxyConfig(BaseModel):
    proxyEnabled: bool = False
    proxyHost: str = ""
    proxyPort: int = 0


dict_engine = DictionaryEngine()
chinese_dict_engine = ChineseDictionaryEngine()

models_file = os.path.join(DATA_DIR, "idic_models.json")
proxy_file = os.path.join(DATA_DIR, "idic_proxy.json")
cache_file = os.path.join(DATA_DIR, "idic_cache.json")
history_file = os.path.join(DATA_DIR, "idic_history.json")

model_list = []
active_model_id = ""

proxy_config = {
    "proxyEnabled": False,
    "proxyHost": "",
    "proxyPort": 0
}

query_cache = {}
query_history = []


def load_cache():
    """加载查询缓存"""
    global query_cache
    if os.path.exists(cache_file):
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                query_cache = json.load(f)
            print(f"加载缓存，共 {len(query_cache)} 条记录")
        except Exception as e:
            print(f"加载缓存失败: {e}")


def save_cache():
    """保存查询缓存"""
    try:
        os.makedirs(os.path.dirname(cache_file), exist_ok=True)
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(query_cache, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"保存缓存失败: {e}")


def load_history():
    """加载查询历史"""
    global query_history
    if os.path.exists(history_file):
        try:
            with open(history_file, "r", encoding="utf-8") as f:
                query_history = json.load(f)
            print(f"加载历史，共 {len(query_history)} 条记录")
        except Exception as e:
            print(f"加载历史失败: {e}")


def save_history():
    """保存查询历史"""
    try:
        os.makedirs(os.path.dirname(history_file), exist_ok=True)
        with open(history_file, "w", encoding="utf-8") as f:
            json.dump(query_history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"保存历史失败: {e}")


def add_to_history(word, direction):
    """添加查询到历史记录"""
    global query_history
    for i, item in enumerate(query_history):
        if item.get("word") == word and item.get("direction") == direction:
            query_history.pop(i)
            break
    query_history.insert(0, {
        "word": word,
        "direction": direction,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    if len(query_history) > 50:
        query_history = query_history[:50]
    save_history()


def get_cache_key(word, direction):
    """生成缓存键"""
    key = f"{word}_{direction}"
    return hashlib.md5(key.encode()).hexdigest()


def load_models():
    """加载多模型配置"""
    global model_list, active_model_id
    if os.path.exists(models_file):
        try:
            with open(models_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            model_list = data.get("models", [])
            active_model_id = data.get("activeModelId", "")
            print(f"加载模型配置，共 {len(model_list)} 个模型，活跃: {active_model_id}")
        except Exception as e:
            print(f"加载模型配置失败: {e}")
    else:
        migrate_old_config()


def save_models():
    """保存多模型配置"""
    try:
        os.makedirs(os.path.dirname(models_file), exist_ok=True)
        data = {
            "models": model_list,
            "activeModelId": active_model_id
        }
        with open(models_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"保存模型配置失败: {e}")


def migrate_old_config():
    """从旧的单模型配置迁移"""
    global model_list, active_model_id
    old_config_file = os.path.join(DATA_DIR, "idic_config.json")
    if os.path.exists(old_config_file):
        try:
            with open(old_config_file, "r", encoding="utf-8") as f:
                old = json.load(f)
            if old.get("apiKey"):
                new_id = str(uuid.uuid4())
                model_list.append({
                    "id": new_id,
                    "name": old.get("modelName", "默认模型"),
                    "modelName": old.get("modelName", ""),
                    "apiKey": old.get("apiKey", ""),
                    "apiBase": old.get("apiBase", ""),
                    "timeout": old.get("timeout", 60)
                })
                active_model_id = new_id
                save_models()
                print(f"从旧配置迁移成功，模型: {old.get('modelName', '')}")
        except Exception as e:
            print(f"从旧配置迁移失败: {e}")


def get_active_config():
    """获取当前活跃模型的配置字典"""
    for m in model_list:
        if m["id"] == active_model_id:
            return {
                "api_base": m.get("apiBase", ""),
                "api_key": m.get("apiKey", ""),
                "model": m.get("modelName", ""),
                "proxies": get_proxy_dict(),
                "timeout": m.get("timeout", 60)
            }
    if model_list:
        return {
            "api_base": model_list[0].get("apiBase", ""),
            "api_key": model_list[0].get("apiKey", ""),
            "model": model_list[0].get("modelName", ""),
            "proxies": get_proxy_dict(),
            "timeout": model_list[0].get("timeout", 60)
        }
    return {
        "api_base": "",
        "api_key": "",
        "model": "",
        "proxies": get_proxy_dict(),
        "timeout": 60
    }


def load_proxy_config():
    """加载代理配置"""
    global proxy_config
    if os.path.exists(proxy_file):
        try:
            with open(proxy_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                proxy_config.update(data)
            print(f"代理配置加载: enabled={proxy_config['proxyEnabled']}, host={proxy_config['proxyHost']}, port={proxy_config['proxyPort']}")
        except Exception as e:
            print(f"加载代理配置失败: {e}")


def save_proxy_config():
    """保存代理配置"""
    try:
        os.makedirs(os.path.dirname(proxy_file), exist_ok=True)
        with open(proxy_file, "w", encoding="utf-8") as f:
            json.dump(proxy_config, f, ensure_ascii=False, indent=2)
        print("代理配置保存成功!")
    except Exception as e:
        print(f"保存代理配置失败: {e}")


def get_proxy_dict():
    """获取 requests 库可用的代理字典"""
    if proxy_config.get("proxyEnabled") and proxy_config.get("proxyHost") and proxy_config.get("proxyPort"):
        proxy_url = f"http://{proxy_config['proxyHost']}:{proxy_config['proxyPort']}"
        return {"http": proxy_url, "https": proxy_url}
    return None


load_models()
load_proxy_config()
load_cache()
load_history()


@app.get("/models")
async def get_models():
    """获取所有模型配置"""
    return {
        "models": model_list,
        "activeModelId": active_model_id
    }


@app.post("/models")
async def add_model(item: ModelConfigItem):
    """添加新模型配置"""
    global active_model_id
    try:
        new_id = item.id or str(uuid.uuid4())
        for m in model_list:
            if m["id"] == new_id:
                return {"success": False, "message": "模型ID已存在"}
        model_item = {
            "id": new_id,
            "name": item.name or item.modelName,
            "modelName": item.modelName,
            "apiKey": item.apiKey,
            "apiBase": item.apiBase,
            "timeout": item.timeout,
            "testResult": item.testResult,
            "testSuccess": item.testSuccess,
            "testTime": item.testTime
        }
        model_list.append(model_item)
        if not active_model_id:
            active_model_id = new_id
        save_models()
        return {"success": True, "message": "模型已添加", "id": new_id}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"success": False, "message": "操作失败，请检查配置"}


@app.put("/models/{model_id}")
async def update_model(model_id: str, item: ModelConfigItem):
    """更新模型配置"""
    try:
        for i, m in enumerate(model_list):
            if m["id"] == model_id:
                model_list[i] = {
                    "id": model_id,
                    "name": item.name or item.modelName,
                    "modelName": item.modelName,
                    "apiKey": item.apiKey,
                    "apiBase": item.apiBase,
                    "timeout": item.timeout,
                    "testResult": item.testResult,
                    "testSuccess": item.testSuccess,
                    "testTime": item.testTime
                }
                save_models()
                return {"success": True, "message": "模型已更新"}
        return {"success": False, "message": "模型不存在"}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"success": False, "message": "操作失败，请检查配置"}


@app.delete("/models/{model_id}")
async def delete_model(model_id: str):
    """删除模型配置"""
    global active_model_id
    try:
        for i, m in enumerate(model_list):
            if m["id"] == model_id:
                model_list.pop(i)
                if active_model_id == model_id:
                    active_model_id = model_list[0]["id"] if model_list else ""
                save_models()
                return {"success": True, "message": "模型已删除"}
        return {"success": False, "message": "模型不存在"}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"success": False, "message": "操作失败，请检查配置"}


@app.post("/models/active/{model_id}")
async def set_active_model(model_id: str):
    """设置活跃模型"""
    global active_model_id
    try:
        for m in model_list:
            if m["id"] == model_id:
                active_model_id = model_id
                save_models()
                return {"success": True, "message": "已切换模型"}
        return {"success": False, "message": "模型不存在"}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"success": False, "message": "操作失败，请检查配置"}


def _update_model_test_result(model_id, result_msg, success, test_time=""):
    """更新模型的测试结果"""
    if not model_id:
        return
    for i, m in enumerate(model_list):
        if m["id"] == model_id:
            model_list[i]["testResult"] = result_msg
            model_list[i]["testSuccess"] = success
            model_list[i]["testTime"] = test_time
            save_models()
            return


@app.post("/test")
async def test_connection(config: ModelConfigItem):
    """测试大模型连接API"""
    import time as _time
    import requests as _requests
    try:
        if not config.apiKey:
            return {"success": False, "message": "API Key 未填写"}

        api_url = config.apiBase.strip().rstrip("/")
        if api_url.endswith("/chat/completions"):
            resolved_url = api_url
        elif re.search(r"/(v\d+|api/v\d+)$", api_url):
            resolved_url = api_url + "/chat/completions"
        else:
            resolved_url = api_url + "/v1/chat/completions"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config.apiKey}",
        }
        payload = {
            "model": config.modelName,
            "messages": [
                {"role": "user", "content": "你是什么大模型"}
            ],
            "max_tokens": 256,
            "chat_template_kwargs": {"enable_thinking": False, "clear_thinking": True},
        }

        start_time = _time.time()
        response = _requests.post(
            resolved_url,
            headers=headers,
            json=payload,
            timeout=config.timeout,
            proxies=get_proxy_dict(),
        )
        elapsed = round(_time.time() - start_time, 2)

        if response.status_code == 200:
            data = response.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            usage = data.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            total_tokens = usage.get("total_tokens", 0)

            tokens_per_sec = round(completion_tokens / elapsed, 1) if elapsed > 0 else 0

            test_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            stats = f"\n\n--- 统计信息 ---\n测试时间: {test_time}\n总耗时: {elapsed}s\nPrompt Tokens: {prompt_tokens}\nCompletion Tokens: {completion_tokens}\nTotal Tokens: {total_tokens}\n生成速度: {tokens_per_sec} tokens/s"
            result_msg = content + stats

            _update_model_test_result(config.id, result_msg, True, test_time)

            return {"success": True, "message": result_msg, "testTime": test_time}
        else:
            error_msg = response.text[:300]
            result_msg = f"HTTP {response.status_code}: {error_msg}\n耗时: {elapsed}s"
            error_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            _update_model_test_result(config.id, result_msg, False, error_time)

            return {"success": False, "message": result_msg, "testTime": error_time}
    except Exception as e:
        import traceback
        traceback.print_exc()
        result_msg = f"连接失败: {str(e)}"
        error_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        _update_model_test_result(config.id, result_msg, False, error_time)

        return {"success": False, "message": result_msg, "testTime": error_time}


@app.delete("/cache")
async def clear_cache(word: str, direction: str = "en2zh"):
    """清除指定查询的缓存"""
    global query_cache
    cache_key = get_cache_key(word, direction)
    if cache_key in query_cache:
        del query_cache[cache_key]
        save_cache()
        return {"success": True, "message": "缓存已清除"}
    return {"success": True, "message": "无缓存"}


@app.post("/proxy")
async def save_proxy_api(config: ProxyConfig):
    """保存代理配置API"""
    try:
        proxy_config["proxyEnabled"] = config.proxyEnabled
        proxy_config["proxyHost"] = config.proxyHost
        proxy_config["proxyPort"] = config.proxyPort
        save_proxy_config()
        return {"success": True, "message": "代理配置已保存"}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"success": False, "message": "操作失败，请检查配置"}


@app.get("/proxy")
async def get_proxy():
    """获取代理配置API"""
    return proxy_config


@app.get("/history")
async def get_history():
    """获取查询历史API"""
    return query_history[:10]


@app.get("/dict")
async def query_dict(word: str):
    """查询本地词典API"""
    try:
        has_chinese = any('\u4e00' <= c <= '\u9fff' for c in word)
        if has_chinese:
            res = chinese_dict_engine.lookup(word)
            if res:
                html = []
                for item in res:
                    html.append(f"<p><strong>{item['simplified']}</strong> ({item['pinyin']})</p>")
                    for defn in item['definitions']:
                        html.append(f"<p>• {defn}</p>")
                    html.append("<br>")
                return "".join(html)
        else:
            res = dict_engine.lookup(word)
            if res:
                parts = []
                if res.get('phonetic'):
                    parts.append(f"<p><strong style='color: #409EFF;'>{res['phonetic']}</strong></p>")
                if res.get('translations'):
                    parts.append("<p><strong>中文释义：</strong></p>")
                    for t in res['translations']:
                        parts.append(f"<p>• {t}</p>")
                return "".join(parts)
        return "<p>暂无词典释义</p>"
    except Exception as e:
        return "<p>查询失败，请稍后重试</p>"


@app.get("/suggest")
async def suggest_words(prefix: str, limit: int = 10):
    """根据前缀获取单词建议API"""
    try:
        has_chinese = any('\u4e00' <= c <= '\u9fff' for c in prefix)
        if has_chinese:
            return {"suggestions": []}
        suggestions = dict_engine.suggest(prefix, limit)
        return {"suggestions": suggestions}
    except Exception as e:
        return {"suggestions": [], "error": "查询失败"}


@app.get("/ai")
async def query_ai(word: str, direction: str = "en2zh"):
    """AI解析查询API"""
    try:
        cache_key = get_cache_key(word, direction)

        if cache_key in query_cache:
            print(f"使用缓存: {word}")
            add_to_history(word, direction)
            return query_cache[cache_key]

        config = get_active_config()

        if not config["api_key"]:
            return "<p style='color: #F56C6C;'>请先在模型配置中设置 API Key</p>"

        if not config["api_base"]:
            config["api_base"] = "https://ark.cn-beijing.volces.com/api/v3"

        translator = Translator(config)
        result = translator.analyze_word(word, direction)
        result = result.replace("\n", "<br>")

        query_cache[cache_key] = result
        save_cache()

        add_to_history(word, direction)

        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"<p style='color: #F56C6C;'>AI 解析失败，请检查您的配置</p>"


@app.get("/ai/stream")
async def query_ai_stream(word: str, direction: str = "en2zh"):
    """AI解析流式查询API（SSE）"""
    config = get_active_config()

    if not config["api_key"]:
        def error_gen():
            yield "data: 请先在模型配置中设置 API Key\n\n"
        return StreamingResponse(error_gen(), media_type="text/event-stream")

    if not config["api_base"]:
        config["api_base"] = "https://ark.cn-beijing.volces.com/api/v3"

    cache_key = get_cache_key(word, direction)
    if cache_key in query_cache:
        print(f"使用缓存: {word}")
        add_to_history(word, direction)
        cached = query_cache[cache_key]

        def cached_gen():
            yield f"data: {json.dumps({'content': cached}, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"
        return StreamingResponse(cached_gen(), media_type="text/event-stream")

    def stream_generate():
        full_result = ""
        usage_data = {}
        try:
            translator = Translator(config)
            for content, usage in translator.analyze_word_stream(word, direction):
                if usage:
                    usage_data = usage
                    continue

                if content:
                    full_result += content
                    yield f"data: {json.dumps({'content': content}, ensure_ascii=False)}\n\n"

            cache_value = full_result.replace("\n", "<br>")
            query_cache[cache_key] = cache_value
            save_cache()
            add_to_history(word, direction)

            if usage_data:
                yield f"data: {json.dumps({'usage': usage_data}, ensure_ascii=False)}\n\n"

            yield "data: [DONE]\n\n"
        except Exception as e:
            import traceback
            traceback.print_exc()
            yield f"data: {json.dumps({'error': 'AI 解析失败，请检查配置'}, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(stream_generate(), media_type="text/event-stream")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
