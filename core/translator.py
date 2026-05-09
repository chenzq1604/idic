"""大模型翻译引擎，兼容OpenAI API格式，支持流式输出"""
import json
import time
import re
import logging

logger = logging.getLogger(__name__)


class LLMTranslator:
    """大模型翻译引擎，支持兼容OpenAI API格式的各种大模型，支持流式输出"""

    def __init__(self, config):
        if isinstance(config, dict):
            self.api_key = config.get('api_key', '')
            self.api_base = config.get('api_base', config.get('api_url', ''))
            self.model = config.get('model', config.get('model_id', ''))
            self.proxies = config.get('proxies', None)
            self.timeout = config.get('timeout', 60)
        else:
            self.api_key = config.api_key
            self.api_base = config.api_base
            self.model = config.model
            self.proxies = getattr(config, 'proxies', None)
            self.timeout = getattr(config, 'timeout', 60)

        self._resolved_url = self._normalize_api_url(self.api_base)

    @staticmethod
    def _normalize_api_url(url):
        """规范化API URL，自动拼接/chat/completions路径

        支持以下输入格式:
        - https://api.openai.com/v1/chat/completions     (完整地址，直接使用)
        - https://api.openai.com/v1                      (自动拼接 /chat/completions)
        - https://api.deepseek.com                       (自动拼接 /v1/chat/completions)
        - https://ark.cn-beijing.volces.com/api/v3       (火山引擎，自动拼接 /chat/completions)
        - https://integrate.api.nvidia.com/v1            (NVIDIA，自动拼接 /chat/completions)
        """
        if not url:
            return url

        url = url.strip().rstrip("/")

        if url.endswith("/chat/completions"):
            return url

        if re.search(r"/(v\d+|api/v\d+)$", url):
            return url + "/chat/completions"

        return url + "/v1/chat/completions"

    def _create_openai_client(self):
        """创建 OpenAI 客户端"""
        from openai import OpenAI
        kwargs = {
            "api_key": self.api_key,
            "base_url": self.api_base.rstrip("/") if self.api_base else None,
            "timeout": self.timeout,
        }
        if self.proxies:
            http_client = None
            try:
                import httpx
                proxy_url = self.proxies.get("https") or self.proxies.get("http")
                if proxy_url:
                    http_client = httpx.Client(proxy=proxy_url, timeout=self.timeout)
            except Exception:
                pass
            if http_client:
                kwargs["http_client"] = http_client
        return OpenAI(**kwargs)

    def translate(self, text, source_lang="auto"):
        """翻译文本，自动检测中英互译方向"""
        if not text or not text.strip():
            return ""
        prompt = self._build_translate_prompt(text, source_lang)
        return self._call_api(prompt)

    def translate_zh2en(self, text):
        """将中文翻译为英文"""
        if not text or not text.strip():
            return ""
        prompt = f"请将以下中文翻译为英文，只返回翻译结果，不要添加额外说明：\n\n{text}"
        return self._call_api(prompt)

    def translate_en2zh(self, text):
        """将英文翻译为中文"""
        if not text or not text.strip():
            return ""
        prompt = f"请将以下英文翻译为中文，只返回翻译结果，不要添加额外说明：\n\n{text}"
        return self._call_api(prompt)

    def analyze_word(self, word, direction="en2zh"):
        """分析单词，返回详细的词义解析和例句"""
        if not word or not word.strip():
            return ""
        prompt = self._build_analyze_prompt(word, direction)
        return self._call_api(prompt)

    def analyze_word_stream(self, word, direction="en2zh"):
        """分析单词，流式返回生成器，yield (content, usage) 元组"""
        if not word or not word.strip():
            return
        prompt = self._build_analyze_prompt(word, direction)
        for chunk in self._call_api_stream(prompt):
            yield (chunk, None)

    def test_connection(self):
        """测试API连接，返回(是否成功, 响应信息, 耗时)"""
        if not self.api_key or not self.api_base:
            return False, "API Key或API URL未配置", 0

        start_time = time.time()
        try:
            client = self._create_openai_client()
            response = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Hello, please reply with 'OK'."}],
                max_tokens=10,
            )
            elapsed = round(time.time() - start_time, 2)
            reply = response.choices[0].message.content if response.choices else ""
            return True, f"连接成功，响应: {reply} ({elapsed}s)\n请求地址: {self._resolved_url}", elapsed
        except Exception as e:
            elapsed = round(time.time() - start_time, 2)
            return False, f"错误: {str(e)} ({elapsed}s)", elapsed

    def _call_api(self, prompt):
        """调用大模型API（非流式，收集完整结果）"""
        if not self.api_key or not self.api_base:
            return "错误：未配置大模型API，请在设置中配置。"

        try:
            client = self._create_openai_client()
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的英汉/汉英翻译助手，提供准确、地道的翻译。"},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=4096,
            )
            return response.choices[0].message.content if response.choices else ""
        except Exception as e:
            logger.error(f"翻译异常: {e}")
            return f"翻译出错: {str(e)}"

    def _call_api_stream(self, prompt):
        """调用大模型API（流式，逐块返回）"""
        if not self.api_key or not self.api_base:
            yield "错误：未配置大模型API，请在设置中配置。"
            return

        try:
            client = self._create_openai_client()
            stream = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的英汉/汉英翻译助手，提供准确、地道的翻译。"},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=4096,
                stream=True,
            )
            for chunk in stream:
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta
                if delta.content:
                    yield delta.content
        except Exception as e:
            logger.error(f"翻译异常: {e}")
            yield f"\n翻译出错: {str(e)}"

    def _build_translate_prompt(self, text, source_lang):
        """构建翻译提示词"""
        has_chinese = any('\u4e00' <= ch <= '\u9fff' for ch in text)
        if has_chinese:
            return f"请将以下中文翻译为英文，只返回翻译结果，不要添加额外说明：\n\n{text}"
        else:
            return f"请将以下英文翻译为中文，只返回翻译结果，不要添加额外说明：\n\n{text}"

    def _build_analyze_prompt(self, word, direction="en2zh"):
        """构建单词/词语分析提示词"""
        has_chinese = any('\u4e00' <= ch <= '\u9fff' for ch in word)
        if has_chinese:
            if direction == "zh2en":
                return self._build_chinese_analyze_en_prompt(word)
            else:
                return self._build_chinese_analyze_prompt(word)
        else:
            return self._build_english_analyze_prompt(word)

    def _build_english_analyze_prompt(self, word):
        """构建英文单词分析提示词"""
        return (
            f"请详细分析以下英文单词，严格按以下格式输出：\n\n"
            f"## 音标\n"
            f"英音 /xxx/  美音 /xxx/\n\n"
            f"## 释义\n"
            f"按词性分类列出中文释义，每项一行：\n"
            f"- [词性] 释义\n\n"
            f"## 例句\n"
            f"每个词性至少1个例句，格式：\n"
            f"- 英文例句\n"
            f"  中文翻译\n\n"
            f"## 搭配\n"
            f"列出3-5个常见搭配或短语\n\n"
            f"## 词根与词源\n"
            f"详细分析该单词的词根构成，格式如下：\n"
            f"- **词根/词缀拆分**：将单词拆分为词根、前缀、后缀，逐个列出\n"
            f"- **词根来源**：每个词根/词缀的来源语言（如拉丁语、希腊语、古法语等）及原始含义\n"
            f"- **构词逻辑**：说明词根和词缀如何组合形成当前单词的含义\n"
            f"- **同根词**：列出3-5个含有相同词根的其他单词，帮助联想记忆\n"
            f"如果该单词无法拆分词根（如基础词汇），则说明其历史演变过程\n\n"
            f"单词: {word}"
        )

    def _build_chinese_analyze_en_prompt(self, word):
        """构建中文词语的英文分析提示词（中→英方向）"""
        is_idiom = len(word) == 4 and all('\u4e00' <= ch <= '\u9fff' for ch in word)
        is_single_char = len(word) == 1 and '\u4e00' <= word <= '\u9fff'

        if is_idiom:
            return (
                f"请分析以下中文成语，严格按以下格式输出：\n\n"
                f"## 英文翻译\n"
                f"最贴切的英文翻译，附上国际音标（IPA），如有多个含义分别列出，格式：\n"
                f"- 英文单词 /国际音标/ 中文释义说明\n\n"
                f"## 词根与词源\n"
                f"对英文翻译中的核心单词进行词根分析，格式如下：\n"
                f"- **词根/词缀拆分**：将单词拆分为词根、前缀、后缀\n"
                f"- **词根来源**：每个词根/词缀的来源语言及原始含义\n"
                f"- **构词逻辑**：词根和词缀如何组合形成当前含义\n"
                f"- **同根词**：列出3-5个含有相同词根的其他单词\n\n"
                f"## 出处\n"
                f"成语的出处或典故\n\n"
                f"## 例句\n"
                f"至少2个例句，格式：\n"
                f"- 中文例句\n"
                f"  English translation\n\n"
                f"## 近义词 / 反义词\n"
                f"列出相关词语及英文对应\n\n"
                f"成语: {word}"
            )
        elif is_single_char:
            return (
                f"请分析以下汉字，严格按以下格式输出：\n\n"
                f"## 英文翻译\n"
                f"按读音分类列出各含义的英文翻译，附上国际音标（IPA），格式：\n"
                f"- 英文单词 /国际音标/ 中文释义说明\n\n"
                f"## 词根与词源\n"
                f"对英文翻译中的核心单词进行词根分析\n\n"
                f"## 例句\n"
                f"每个读音至少1个例句\n\n"
                f"## 常见组词\n"
                f"列出5-8个常见组词及其英文翻译\n\n"
                f"汉字: {word}"
            )
        else:
            return (
                f"请分析以下中文词语，严格按以下格式输出：\n\n"
                f"## 英文翻译\n"
                f"最贴切的英文翻译，附上国际音标（IPA）和词性标注，如有多个含义分别列出，格式：\n"
                f"- 英文单词 /国际音标/ 词性  中文释义说明\n\n"
                f"## 词根与词源\n"
                f"对英文翻译中的核心单词进行词根分析\n\n"
                f"## 常见短语\n"
                f"列出5-8个包含该词的常见短语或搭配\n\n"
                f"## 例句\n"
                f"至少2个例句\n\n"
                f"词语: {word}"
            )

    def _build_chinese_analyze_prompt(self, word):
        """构建中文词语分析提示词"""
        is_idiom = len(word) == 4 and all('\u4e00' <= ch <= '\u9fff' for ch in word)
        is_single_char = len(word) == 1 and '\u4e00' <= word <= '\u9fff'

        if is_idiom:
            return (
                f"请详细分析以下成语，严格按以下格式输出：\n\n"
                f"## 拼音\n完整拼音（含声调）\n\n"
                f"## 释义\n详细解释成语的含义\n\n"
                f"## 出处\n成语的出处或典故\n\n"
                f"## 例句\n至少2个例句\n\n"
                f"## 近义词 / 反义词\n列出相关词语\n\n"
                f"成语: {word}"
            )
        elif is_single_char:
            return (
                f"请详细分析以下汉字，严格按以下格式输出：\n\n"
                f"## 拼音\n所有读音及对应释义\n\n"
                f"## 释义\n按读音分类列出释义\n\n"
                f"## 例句\n每个读音至少1个例句\n\n"
                f"## 组词\n列出5-8个常见组词\n\n"
                f"## 笔画\n总笔画数、部首\n\n"
                f"汉字: {word}"
            )
        else:
            return (
                f"请详细分析以下中文词语，严格按以下格式输出：\n\n"
                f"## 拼音\n完整拼音（含声调）\n\n"
                f"## 释义\n详细解释词语的含义\n\n"
                f"## 例句\n至少2个例句\n\n"
                f"## 近义词 / 反义词\n列出相关词语\n\n"
                f"## 英文对应\n最贴切的英文翻译及用法说明\n\n"
                f"词语: {word}"
            )
