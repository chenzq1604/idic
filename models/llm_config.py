"""大模型配置数据模型"""
import json
import os
from datetime import datetime
from utils.paths import get_writable_path


class LLMConfig:
    """大模型配置类，存储单个大模型的连接信息"""

    def __init__(self, name="", api_key="", api_base="", api_url="",
                 model_name="", model_id="",
                 is_active=False, created_at=None, test_result=None):
        self.name = name
        self.api_key = api_key
        self.api_base = api_base or api_url
        self.model_name = model_name or model_id
        self.is_active = is_active
        self.created_at = created_at or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.test_result = test_result

    def to_dict(self):
        """将配置转换为字典"""
        return {
            "name": self.name,
            "api_key": self.api_key,
            "api_base": self.api_base,
            "api_url": self.api_base,  # 兼容旧字段
            "model_name": self.model_name,
            "model_id": self.model_name,  # 兼容旧字段
            "is_active": self.is_active,
            "created_at": self.created_at,
            "test_result": self.test_result,
        }

    @classmethod
    def from_dict(cls, data):
        """从字典创建配置对象"""
        return cls(
            name=data.get("name", ""),
            api_key=data.get("api_key", ""),
            api_base=data.get("api_base", data.get("api_url", "")),  # 兼容旧字段
            model_name=data.get("model_name", data.get("model_id", "")),  # 兼容旧字段
            is_active=data.get("is_active", False),
            created_at=data.get("created_at", ""),
            test_result=data.get("test_result", None),
        )


class LLMConfigManager:
    """大模型配置管理器，负责配置的增删改查和持久化"""

    CONFIG_FILE = get_writable_path("llm_configs.json")

    def __init__(self):
        self.configs = []
        self.load()

    def load(self):
        """从文件加载配置"""
        if os.path.exists(self.CONFIG_FILE):
            try:
                with open(self.CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.configs = [LLMConfig.from_dict(d) for d in data]
            except (json.JSONDecodeError, IOError):
                self.configs = []
        else:
            self.configs = []

    def save(self):
        """保存配置到文件"""
        os.makedirs(os.path.dirname(self.CONFIG_FILE), exist_ok=True)
        with open(self.CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump([c.to_dict() for c in self.configs], f,
                      ensure_ascii=False, indent=2)

    def add(self, config):
        """添加配置"""
        self.configs.append(config)
        self.save()

    def add_config(self, config_dict):
        """直接添加字典配置（新的API）"""
        self.configs.append(LLMConfig.from_dict(config_dict))
        self.save()

    def remove(self, index):
        """删除配置"""
        if 0 <= index < len(self.configs):
            self.configs.pop(index)
            self.save()

    def update(self, index, config):
        """更新配置"""
        if 0 <= index < len(self.configs):
            self.configs[index] = config
            self.save()

    def list_configs(self):
        """列出所有配置（兼容原来的字典形式）"""
        return [c.to_dict() for c in self.configs]

    def get_active(self):
        """获取当前激活的配置"""
        for config in self.configs:
            if config.is_active:
                return config
        return None

    def set_active(self, index):
        """设置激活的配置"""
        for i, config in enumerate(self.configs):
            config.is_active = (i == index)
        self.save()

    def update_test_result(self, index, result):
        """更新测试结果"""
        if 0 <= index < len(self.configs):
            self.configs[index].test_result = result
            self.save()
